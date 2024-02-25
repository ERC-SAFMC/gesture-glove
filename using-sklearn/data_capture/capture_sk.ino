#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
#include "Wire.h"
#endif

MPU6050 mpu(0x69); // <-- use for AD0 high
#define OUTPUT_READABLE_YAWPITCHROLL

#define INTERRUPT_PIN 2
#define LED_PIN 13
bool blinkState = false;

uint8_t mpuIntStatus;
uint8_t devStatus;
bool dmpReady = false;
uint16_t packetSize;
uint8_t fifoBuffer[64];
volatile bool mpuInterrupt = false;

Quaternion q;           // [w, x, y, z]         quaternion container
VectorInt16 aa;         // [x, y, z]            accel sensor measurements
VectorInt16 gyro;
VectorInt16 aaReal;     // [x, y, z]            gravity-free accel sensor measurements
VectorInt16 aaWorld;    // [x, y, z]            world-frame accel sensor measurements
VectorFloat gravity;    // [x, y, z]            gravity vector
float euler[3];         // [psi, theta, phi]    Euler angle container
float ypr[3];

//#define SAMPLING_MODE
#define MAX_DATA_TO_PRINT 100
uint16_t dataCount = 0;
bool printData = false;

void dmpDataReady() {
    mpuInterrupt = true;
}


void setup() {
    #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    Wire.begin();
    Wire.setClock(400000);
    #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(400, true);
    #endif

    Serial.begin(115200);
    while (!Serial);
    
//    Serial.println(F("Initializing I2C devices..."));
    mpu.initialize();
    pinMode(INTERRUPT_PIN, INPUT);

//    Serial.println(F("Testing device connections..."));
//    Serial.println(mpu.testConnection() ? F("MPU6050 connection successful") : F("MPU6050 connection failed"));

//    Serial.println(F("\nSend any character to begin DMP programming and demo: "));
//    while (Serial.available() && Serial.read());
//    while (!Serial.available());
//    while (Serial.available() && Serial.read());

//    Serial.println(F("Initializing DMP..."));
    if (mpu.dmpInitialize() == 0) {
        mpu.setXGyroOffset(-75);
        mpu.setYGyroOffset(-4);
        mpu.setZGyroOffset(-64);
        mpu.setXAccelOffset(-3590);
        mpu.setYAccelOffset(-3937);
        mpu.setZAccelOffset(1120);

        mpu.PrintActiveOffsets();
        Serial.println(F("Enabling DMP..."));
        mpu.setDMPEnabled(true);

//        Serial.print(F("Enabling interrupt detection (Arduino external interrupt "));
        Serial.print(digitalPinToInterrupt(INTERRUPT_PIN));
        Serial.println(F(")..."));
        attachInterrupt(digitalPinToInterrupt(INTERRUPT_PIN), dmpDataReady, RISING);
        mpuIntStatus = mpu.getIntStatus();

        Serial.println(F("DMP ready! Waiting for first interrupt..."));
        dmpReady = true;
        packetSize = mpu.dmpGetFIFOPacketSize();
    } else {
        Serial.print(F("DMP Initialization failed (code "));
        Serial.print(devStatus);
        Serial.println(F(")"));
    }

    pinMode(LED_PIN, OUTPUT);
}

void loop() {
    if (!dmpReady) return;

    if (printData && mpu.dmpGetCurrentFIFOPacket(fifoBuffer)) {
        mpu.dmpGetQuaternion(&q, fifoBuffer);
        mpu.dmpGetGravity(&gravity, &q);
        mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
        mpu.dmpGetAccel(&aa, fifoBuffer);
        mpu.dmpGetGyro(&gyro, fifoBuffer);

        Serial.print("IMU: ");
        Serial.print(aa.x);
        Serial.print(",");
        Serial.print(aa.y);
        Serial.print(",");
        Serial.print(aa.z);
        Serial.print(",");
        Serial.print(gyro.x);
        Serial.print(",");
        Serial.print(gyro.z);
        Serial.print(",");
        Serial.print(gyro.z);
        Serial.print("\n");
        
        blinkState = !blinkState;
        digitalWrite(LED_PIN, blinkState);
    }
}
