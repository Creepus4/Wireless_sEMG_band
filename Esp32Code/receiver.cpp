#include <esp_now.h>
#include <WiFi.h>
#include <esp_wifi.h>

#define NUM_CHANNELS 3
#define BATCH_SIZE 32 //define nr of data points in batch
#define SYNC_LINE 0x8080 //sync word

struct sEMGPacket {
  uint16_t sync;
  uint16_t data[BATCH_SIZE * NUM_CHANNELS];
};
sEMGPacket packet; 

QueueHandle_t dataQueue;

//Receive data
void OnDataRecv(const esp_now_recv_info_t *info, const uint8_t *data, int len) { //runs when packet arives
  if (len == BATCH_SIZE * NUM_CHANNELS * sizeof(uint16_t)) {
    xQueueSend(dataQueue, data, 0); //copy packet into dataQueue
  }  
}

//send to computer
void serialTask(void *pvPrameters) {
  uint16_t buffer[BATCH_SIZE * NUM_CHANNELS]; //storage space of one packet in buffer
  
  while(true){
    if (xQueueReceive(dataQueue, buffer, portMAX_DELAY)) { //waits for packet in dataQueue to copy to buffer
      
      packet.sync = SYNC_LINE;
      memcpy(packet.data, buffer, sizeof(buffer));
      
      Serial.write((uint8_t*)&packet, sizeof(packet));
    }
  }
}

void setup() {
  Serial.begin(921600);

  WiFi.mode(WIFI_STA); //station mode esp now
  esp_wifi_set_ps(WIFI_PS_NONE); //no wifi sleep
  esp_wifi_set_channel(1,WIFI_SECOND_CHAN_NONE); //use channel 1 only
  esp_now_init(); //initializes esp now protocol
  esp_now_register_recv_cb(OnDataRecv); //incoming packets trigger OnDataReceiv 

  dataQueue = xQueueCreate(10, BATCH_SIZE * NUM_CHANNELS * sizeof(uint16_t)); //creates queue, 10 packet

  xTaskCreatePinnedToCore(serialTask, "SERIAL", 4096, NULL, 1, NULL, 1); //allocate work to core 1 and prio
}

void loop() {}
