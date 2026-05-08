#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>
#include <driver/adc.h>

#define SAMPLE_RATE 2000
#define SAMPLE_INTERVAL (1000000 / SAMPLE_RATE)
#define BATCH_SIZE 32
#define NUM_CHANNELS 3

adc1_channel_t adcChannels[NUM_CHANNELS] = {ADC1_CHANNEL_1, ADC1_CHANNEL_4, ADC1_CHANNEL_8}; //pins for ADC

uint8_t peerMac[] = {0x80, 0xB5, 0x4E, 0xE3, 0x21, 0x34}; //receiver adress

uint16_t bufferA[BATCH_SIZE * NUM_CHANNELS]; //dubble buffer, sampling and sending
uint16_t bufferB[BATCH_SIZE * NUM_CHANNELS];

volatile uint16_t* activeBuffer = bufferA;
volatile uint16_t* sendBuffer = bufferB;

volatile int bufferIndex = 0;
volatile bool bufferReady = false; //false = sampling, true = send

hw_timer_t* timer = NULL;
portMUX_TYPE timerMux = portMUX_INITIALIZER_UNLOCKED;

TaskHandle_t sendTaskHandle; //for notifying the send task

void IRAM_ATTR onTimer() { //interupt fn runs on timer, IRAM_ATTR puts function in fast memory
  portENTER_CRITICAL_ISR(&timerMux); //safe access

  if (!bufferReady) {
    for (int ch = 0; ch < NUM_CHANNELS; ch++ ) { //data is stored [ch0, ch1, ch2 ...]
      activeBuffer[bufferIndex * NUM_CHANNELS + ch] = adc1_get_raw(adcChannels[ch]);
    }
    bufferIndex++; //increment to next sample slot

    if (bufferIndex >= BATCH_SIZE) { //buffer full
      bufferIndex = 0;

      uint16_t* temp = (uint16_t*)activeBuffer; //buffer swap
      activeBuffer = sendBuffer;
      sendBuffer = temp;

      bufferReady = true; //stop samling

      BaseType_t xHigherPriorityTaskWoken = pdFALSE;
      vTaskNotifyGiveFromISR(sendTaskHandle, &xHigherPriorityTaskWoken); //wake up send task
      if (xHigherPriorityTaskWoken) { //Immediately switch to send task if woken
        portYIELD_FROM_ISR();
      }
    }
  }
  portEXIT_CRITICAL_ISR(&timerMux);
}

void sendTask(void* pvParameters) {
  while (true) { //runs constantely
    ulTaskNotifyTake(pdTRUE, portMAX_DELAY);//sleeps until woken

    portENTER_CRITICAL(&timerMux);
    bufferReady = false; //start samling again
    portEXIT_CRITICAL(&timerMux);

    esp_now_send(peerMac,(uint8_t*)sendBuffer, sizeof(uint16_t) * BATCH_SIZE * NUM_CHANNELS); //send
  }
}

void setup() {
WiFi.mode(WIFI_STA); //station mode esp now
esp_wifi_set_ps(WIFI_PS_NONE); //no wifi sleep

esp_now_init(); //initializes esp now protocol

esp_now_peer_info_t peer = {}; //peer struct
memcpy(peer.peer_addr, peerMac, 6);
peer.channel = 1; 
esp_now_add_peer(&peer);
esp_wifi_set_channel(1, WIFI_SECOND_CHAN_NONE); //use channel 1 only 

xTaskCreatePinnedToCore(sendTask, "SEND", 4096, NULL, 1, &sendTaskHandle, 1); //allocate work to core 1 and prio

timer = timerBegin(1000000); //1 tick = 1us 
timerAttachInterrupt(timer, &onTimer); //attach interrupt 
timerAlarm(timer, SAMPLE_INTERVAL, true, 0); //trigger in sample interval

adc1_config_width(ADC_WIDTH_BIT_12); // 0-4095

adc1_config_channel_atten(ADC1_CHANNEL_1, ADC_ATTEN_DB_11);
adc1_config_channel_atten(ADC1_CHANNEL_4, ADC_ATTEN_DB_11);
adc1_config_channel_atten(ADC1_CHANNEL_8, ADC_ATTEN_DB_11);
}

void loop() {}
