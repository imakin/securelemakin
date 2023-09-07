/**
 * Simple HID keyboard
 * author: chegewara
 */


#include "hidkeyboard.h"

HIDkeyboard dev;

void setup()
{
    Serial.begin(115200);
    dev.begin();
}
void loop()
{
    // dev.senAdChar('A'); // send ASCII char
    delay(2000);
}
