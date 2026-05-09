/* 
This test uses one esp32 microcontroller and stores 
the largest values from channel 4.
To start press reset on the device, you have 5 seconds on you to tense the arm. 
after 5 second the largest value will be printed in the serial monitor. 
To start over press reset button on the device
*/

#include <driver/adc.h>

uint16_t Max_Val = 0;
unsigned long startTime; 

void setup() {
  Serial.begin(115200);

  adc1_config_width(ADC_WIDTH_BIT_12); 
  adc1_config_channel_atten(ADC1_CHANNEL_4, ADC_ATTEN_DB_11);

  startTime = millis ();
}

void loop() {
  if(millis()-startTime < 5000) {
    int rawValue4 = adc1_get_raw(ADC1_CHANNEL_4);
    
    if (rawValue4 > Max_Val) {
      Max_Val = rawValue4;
    }
    delayMicroseconds(1000);
  }
  
  else {
    Serial.println(Max_Val);
    Serial.println("STOP");
    while (true){
      //do nothing
    }
  }
}
