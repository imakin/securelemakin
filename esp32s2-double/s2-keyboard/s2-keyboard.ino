#include "Wire.h"
#include "src/util_arraymalloc.h"
#include "hidkeyboard.h" // using EspTinyUSB / ESP32TinyUSB by krempa/chegewara

String text = "";
bool text_set = false;

#define ledpin 15
#define keyboard_echo_flag_pin 37

char* password;
int passwordlen;
#define passwordmaxlen 64

#define commandmaxlen 128
int commandlen = 0;

#define sda_pin 2
#define scl_pin 4

unsigned long var_uint64;

HIDkeyboard keyboard;

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
            // Serial.println("cmd reset");
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
    // Serial.begin(115200);
    // for (int i=0;i<10;i++){
    //     delay(1000);
    //     Serial.println("ok0");
    // }
    delay(1000);

    pinMode(ledpin, OUTPUT);
    pinMode(keyboard_echo_flag_pin, INPUT);
    digitalWrite(keyboard_echo_flag_pin, LOW);
    digitalWrite(ledpin, LOW);

/*
        self.bt_left = Pin(12,Pin.PULL_UP)
        self.bt_right = Pin(35,Pin.PULL_UP)
        self.bt_ok = Pin(33,Pin.PULL_UP)
        let s2-secure control those pin
        */
    pinMode(12,INPUT);
    pinMode(35,INPUT);
    pinMode(33,INPUT);

    keyboard.begin();

    Wire.begin(100,sda_pin,scl_pin,100000);//address=100 as slave, leonardo (D2 SDA), (D3 SCL). on esp: (D2 GPIO4 SDA) (D1 GPIO5 SCL)
    cmd.clear();
    Wire.onReceive(wireOnReceive);
    Wire.onRequest(wireOnRequest);
    
    // keyboard.sendChar('B');
    // delay(1000);
    // keyboard.sendChar('i');
    // delay(1000);
    // keyboard.sendChar('s');
    // delay(1000);
}


void loop() {
    char chr;
    bool ngisi = false;
    // while (Serial.available()>0){
    //     chr = (char)Serial.read();
    //     while (cmd.is_sending);
    //     cmd.append(chr);
    //     ngisi = true;
    // }
    // if (ngisi) {
    //     cmd.append(0);
    //     Serial.print("pos_fill: ");
    //     Serial.println(cmd.pos_fill);
    // }
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
    else if (c>=32 && c<=126){
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
        digitalWrite(ledpin,HIGH);
    }
    else {
        digitalWrite(ledpin,LOW);
    }
    //~ text = "";
    //~ bool text_set = false;
    while (Wire.available()) {
        char c = Wire.read();
        // cmd.append(c+1);
        if (keyboardmode) {
            digitalWrite(ledpin,HIGH);
            if (is_printable(c)){
                keyboard.sendChar(c);
                delay(25);
            }
            else {
                //non printable ascii data
            }
        }
        else {
            //flag pin is not high, echo back to USB-Host
            //~ text += c;
            //~ text_set = true;
            // Serial.write(c);
        }
    }
    digitalWrite(ledpin,LOW);
    //~ Serial.print("received: ");
    //~ Serial.println(received_length);
}


