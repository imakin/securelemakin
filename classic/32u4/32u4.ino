#include "Keyboard.h"
#include "Wire.h"
#include "src/util_arraymalloc.h"


String text = "";
bool text_set = false;

bool is_serial_capturingpassword = false;

int8_t keyboard_echo_flag_pin = 6;

char* password;
int passwordlen;
#define passwordmaxlen 64

#define commandmaxlen 128
int commandlen = 0;

#define button_a_in A0
#define button_a_out A2
#define button_b_in 9
#define button_b_out 11

unsigned long var_uint64;

class CommandManager{
    public:
        char* data;
        int pos_fill; //position of data to be filled
        int pos_sent; //position of data that has been sent
        int is_sending;
        CommandManager(){
            data = array(char,commandmaxlen);
            pos_fill = 0;
            pos_sent = 0;
            is_sending = false;
        }
        void clear(){
            data[0] = 0;
            pos_fill = 0;
            pos_sent = 0;
            is_sending = false;
        }
        bool is_clear(){
            if (data[0]==0) {
                return true;
            }
            return false;
        }
        bool send_next(int repeat){
            if (data[pos_sent]!=0 && pos_sent<commandmaxlen){
                for (int i=0;i<repeat;i++){
                    Wire.write(data[pos_sent]);
                }
                pos_sent += 1;
                return true;
            }
            clear();
            Serial.println("cmd reset");
            return false;
        }
        bool append(char n){
            if (pos_fill<commandmaxlen){
                data[pos_fill] = n;
                pos_fill += 1;
                return true;
            }
            return false;
        }
};
CommandManager cmd;

void setup(){
    pinMode(keyboard_echo_flag_pin, INPUT);
    digitalWrite(keyboard_echo_flag_pin, LOW);
    delay(1000);
    Serial.begin(115200);
    //~ Serial1.begin(115200);
    Serial.println("ok0");
    //~ Serial1.println("ok1");
    Keyboard.begin();
    Wire.begin(100);//address=1 as slave, leonardo (D2 SDA), (D3 SCL). on esp: (D2 GPIO4 SDA) (D1 GPIO5 SCL)
    Wire.setClock(100000);
    cmd.clear();
    Wire.onReceive(wireOnReceive);
    Wire.onRequest(wireOnRequest);
    pinMode(button_a_out,OUTPUT);
    pinMode(button_b_out,OUTPUT);
    digitalWrite(button_a_out,LOW);
    digitalWrite(button_b_out,LOW);
    
    //~ DDRB = DDRB | 0b01000000;
    //~ PORTB = PORTB & 0b10111111;
    
    pinMode(button_a_in,INPUT_PULLUP);
    pinMode(button_b_in,INPUT_PULLUP);
    
}


void loop() {
    char chr;
    //~ commandlen = 0;
    bool ngisi = false;
    while (Serial.available()>0){
        chr = (char)Serial.read();
        while (cmd.is_sending);
        cmd.append(chr);
        ngisi = true;
    }
    if (ngisi) {
        cmd.append(0);
        Serial.print("pos_fill: ");
        Serial.println(cmd.pos_fill);
    }
    
    //button routine
    char button_value = 0;
    if (digitalRead(button_a_in)==LOW){
        var_uint64 = millis();
        while (digitalRead(button_a_in)==LOW);
        if ((millis()-var_uint64)>1000) {
            button_value = 'C';
        }
        else {
            button_value = 'A';
        }
    }
    if (digitalRead(button_b_in)==LOW){
        var_uint64 = millis();
        while (digitalRead(button_b_in)==LOW);
        if ((millis()-var_uint64)>1000) {
            button_value = 'C';
        }
        else {
            button_value = 'B';
        }
    }
    if (button_value!=0){
        cmd.append('B');
        cmd.append(button_value);
        cmd.append(10);
        cmd.append(0);
    }
}

/**
 * esp8266 only has 1 usable full duplex tx rx already used by python repl. use wire instead.
 * unfortunately the esp8266 micropython only support master mode wire, so 32u4 will act as slave/peripheral
 * 
 * esp will read 128 byte and 32u4 will send data waiting in the queue.
 * data can be filled from USB-HOST 
 * 
 * secure data is stored in esp8266
 * keyboard USB HID and usb interface is handled by 32u4
 * 32u4 may transmit:
 *      securedata-id requested by USB-Host connected in 32u4's USB 
 * 
 * esp8266 may transmit:
 *      securedata typing initiated by 32u4
 *      securedata typing initiated by esp8266's own web service
 */

bool is_printable(uint8_t c){
    if (c==9 || c==10 || c==13){
        return true;
    }
    else if (c>=32 && c<=127){
        return true;
    }
    else {
        //non printable ascii data
        return false;
    }
}
bool is_printable(int8_t c){
    return is_printable((uint8_t)c);
}
bool is_printable(char c){
    return is_printable((uint8_t)c);
}

void wireOnRequest(){
    cmd.is_sending = true;
    cmd.send_next(1);
    //~ for (int i =0;i<32;i++){
        //~ cmd.send_next(1);
    //~ }
    cmd.is_sending = false;
}

void wireOnReceive(int received_length){
    bool keyboardmode = false;
    if (digitalRead(keyboard_echo_flag_pin)==HIGH) {
        //check one and keep the flag even if pin is changing mid i2c data transfer
        keyboardmode = true;
    }
    //~ text = "";
    //~ bool text_set = false;
    while (Wire.available()) {
        char c = Wire.read();
        if (keyboardmode) {
            if (is_printable(c)){
                Keyboard.print(c);
            }
            else {
                //non printable ascii data
            }
        }
        else {
            //flag pin is not high, echo back to USB-Host
            //~ text += c;
            //~ text_set = true;
            Serial.write(c);
        }
    }
    //~ Serial.print("received: ");
    //~ Serial.println(received_length);
}


