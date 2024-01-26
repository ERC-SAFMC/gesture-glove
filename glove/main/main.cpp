#include <driver/i2c.h>
#include <esp_log.h>
#include <esp_err.h>
#include "freertos/FreeRTOS.h"
#include "sdkconfig.h"
#include "freertos/task.h"

#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/micro_op_resolver.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/micro/system_setup.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "model.h"

#include "output_handler.h"

const tflite::Model* model = nullptr;
tflite::MicroInterpreter* interpreter = nullptr;
TfLiteTensor* input = nullptr;
TfLiteTensor* output = nullptr;
int inference_count = 0;

constexpr int kTensorArenaSize = 8 * 1024;
uint8_t tensor_arena[kTensorArenaSize];

// array to map gesture index to a name
const char* GESTURES[] = {
  "left",
   "right",
  "forward",
  "backward",
};

// const int XDirection[]   = { 30, -30, 0, 0 };
// const int YDirection[] = { 0, 0, 30, -30 };

#define NUM_GESTURES (sizeof(GESTURES) / sizeof(GESTURES[0]))
const float accelerationThreshold = 2.5; // threshold of significant in G's
const int numSamples = 100;

int samplesRead = numSamples;

#include "MPU6050_6Axis_MotionApps20.h"

MPU6050 mpu = MPU6050(0x68);
#define PIN_SDA 21
#define PIN_CLK 22

Quaternion q;           // [w, x, y, z]         quaternion container
VectorFloat gravity;    // [x, y, z]            gravity vector
VectorInt16 accel;
VectorInt16 gyro;
VectorInt16 aa;			// [x, y, z]			accel sensor measurements
VectorInt16 aaReal;		// [x, y, z]			gravity-free accel sensor measurements
VectorInt16 aaWorld;	// [x, y, z]			world-frame accel sensor measurements
float ypr[3];           // [yaw, pitch, roll]   yaw/pitch/roll container and gravity vector
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
bool dmpReady = false;

const float kXrange = 2.f * 3.14159265359f;

void task_initI2C(void *ignore) {
	i2c_config_t conf;
	conf.mode = I2C_MODE_MASTER;
	conf.sda_io_num = (gpio_num_t)PIN_SDA;
	conf.scl_io_num = (gpio_num_t)PIN_CLK;
	conf.sda_pullup_en = GPIO_PULLUP_ENABLE;
	conf.scl_pullup_en = GPIO_PULLUP_ENABLE;
	conf.master.clk_speed = 400000;
	ESP_ERROR_CHECK(i2c_param_config(I2C_NUM_0, &conf));
	ESP_ERROR_CHECK(i2c_driver_install(I2C_NUM_0, I2C_MODE_MASTER, 0, 0, 0));
	vTaskDelete(NULL);
}

void tf_setup()
{
	model = tflite::GetModel(g_model);
	if (model->version() != TFLITE_SCHEMA_VERSION) {
    MicroPrintf("Model provided is schema version %d not equal to supported "
                "version %d.", model->version(), TFLITE_SCHEMA_VERSION);
    return;
	}
/* 
	if (tensor_arena == NULL) {
		tensor_arena = (uint8_t *) heap_caps_malloc(kTensorArenaSize, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
	}
*/
    static tflite::MicroMutableOpResolver<4> micro_op_resolver;
	if (micro_op_resolver.AddFullyConnected() != kTfLiteOk) {
		return;
	}

	if (micro_op_resolver.AddReshape() != kTfLiteOk) {
		// Handle error
	}

	if (micro_op_resolver.AddSoftmax() != kTfLiteOk) {
		// Handle error
	}

	if (micro_op_resolver.AddRelu() != kTfLiteOk) {
		// Handle error
	}

	// if (micro_op_resolver.AddActivaetion(tflite::BuiltinOperator_RELU, tflite::ops::micro::Register_RELU()) != kTfLiteOk) {
	// 	// Handle error
	// }
	// if (micro_op_resolver.Add() != kTfLiteOk) {
	// 	return;
	// }
	// if (micro_op_resolver.AddFullyConnected() != kTfLiteOk) {
	// 	return;
	// }
	// if (micro_op_resolver.AddSoftmax() != kTfLiteOk) {
	// 	return;
	// }
	// if (micro_op_resolver.AddReshape() != kTfLiteOk) {
	// 	return;
	// }

	static tflite::MicroInterpreter static_interpreter(
		model, micro_op_resolver, tensor_arena, kTensorArenaSize);
	interpreter = &static_interpreter;

	// Allocate memory from the tensor_arena for the model's tensors.
	TfLiteStatus allocate_status = interpreter->AllocateTensors();
	if (allocate_status != kTfLiteOk) {
		MicroPrintf("AllocateTensors() failed");
		return;
	} else MicroPrintf("AllocateTensors() success");
	
	input = interpreter->input(0);
	output = interpreter->output(0);

	// Keep track of how many inferences we have performed.
	inference_count = 0;
}

void task_display(void*){
	mpu.initialize();
	mpu.dmpInitialize();

	// This need to be setup individually
	mpu.setXGyroOffset(-75);
    mpu.setYGyroOffset(-4);
    mpu.setZGyroOffset(-64);
    mpu.setXAccelOffset(-3590);
    mpu.setYAccelOffset(-3937);
    mpu.setZAccelOffset(1120);
	
	mpu.setDMPEnabled(true);
    packetSize = mpu.dmpGetFIFOPacketSize();
	dmpReady = true;
	printf("Start\n");
	while (1)
	{
		float position = static_cast<float>(inference_count) /
                   static_cast<float>(20);
  		float x = position * kXrange;
		if (!dmpReady) return;

		if (samplesRead == numSamples) samplesRead = 0;

		if (samplesRead < numSamples) {
			if (mpu.dmpGetCurrentFIFOPacket(fifoBuffer))
			{
				mpu.dmpGetQuaternion(&q, fifoBuffer);
				mpu.dmpGetGravity(&gravity, &q);
				mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
				mpu.dmpGetAccel(&aa, fifoBuffer);
				mpu.dmpGetGyro(&gyro, fifoBuffer);

				input->data.f[samplesRead   * 6 + 0] = (aa.x + 16384) / 32768;
				input->data.f[samplesRead * 6 + 1]   = (aa.y + 16384) / 32768;
				input->data.f[samplesRead * 6 + 2] = (aa.z + 16384) / 32768;
				input->data.f[samplesRead * 6 + 3] = (gyro.x + 250) / 500.0;
				input->data.f[samplesRead * 6 + 4] = (gyro.y + 250) / 500.0;
				input->data.f[samplesRead * 6 + 5] = (gyro.z + 250) / 500.0;
				samplesRead++;

				if (samplesRead == numSamples) {
					TfLiteStatus invokeStatus = interpreter->Invoke();
					if (invokeStatus != kTfLiteOk) {
						printf("Invoke Failed!");//change to LOGE
						while (1){};return;
					}
					int result;
					result = -1;
					// for (int i = 0; i < NUM_GESTURES; i++){
					// 	printf(GESTURES[i]);
					// 	printf(": ");
					// 	printf(output->data.f[i]);
					// 	printf(" / ");
					// 	if ( output->data.f[i]   > 0.95) {
					// 		result = i;
					// 	}
					// }
					int8_t y_quantized = output->data.int8[0];
					float y = (y_quantized - output->params.zero_point) * output->params.scale;
					HandleOutput(x, y);
					inference_count += 1;
					// if (inference_count >= kInferencesPerCycle) inference_count = 0;
				}
			}
		}
	}
/* 	while(1){
	    mpuIntStatus = mpu.getIntStatus();
		// get current FIFO count
		fifoCount = mpu.getFIFOCount();

	    if ((mpuIntStatus & 0x10) || fifoCount == 1024) {
	        // reset so we can continue cleanly
	        mpu.resetFIFO();

	    // otherwise, check for DMP data ready interrupt frequently)
	    } else if (mpuIntStatus & 0x02) {
	        // wait for correct available data length, should be a VERY short wait
	        while (fifoCount < packetSize) fifoCount = mpu.getFIFOCount();

	        // read a packet from FIFO
            mpu.getFIFOBytes(fifoBuffer, packetSize);
            mpu.dmpGetQuaternion(&q, fifoBuffer);
            mpu.dmpGetAccel(&aa, fifoBuffer);
            mpu.dmpGetGravity(&gravity, &q);
            mpu.dmpGetLinearAccel(&aaReal, &aa, &gravity);
            mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
            printf("areal x=%d y:%d z:%d\n", aa.x, aa.y, aa.z);

	        // mpu.getFIFOBytes(fifoBuffer, packetSize);
	 		// mpu.dmpGetQuaternion(&q, fifoBuffer);
			// mpu.dmpGetGravity(&gravity, &q);
			// mpu.dmpGetYawPitchRoll(ypr, &q, &gravity);
			printf("YAW: %3.1f, ", ypr[0] * 180/M_PI);
			printf("PITCH: %3.1f, ", ypr[1] * 180/M_PI);
			printf("ROLL: %3.1f \n", ypr[2] * 180/M_PI);
	    }

	    //Best result is to match with DMP refresh rate
	    // Its last value in components/MPU6050/MPU6050_6Axis_MotionApps20.h file line 310
	    // Now its 0x13, which means DMP is refreshed with 10Hz rate
		// vTaskDelay(5/portTICK_PERIOD_MS);
	} */

	vTaskDelete(NULL);
}

extern "C" {
	void app_main(void);
}

extern void task_initI2C(void*);
extern void task_display(void*);

void app_main(void)
{
    xTaskCreate(&task_initI2C, "mpu_init", 2048, NULL, 5, NULL);
    vTaskDelay(500/portTICK_PERIOD_MS);
    tf_setup();
	vTaskDelay(500/portTICK_PERIOD_MS);
    xTaskCreate(&task_display, "imu_task", 8192, NULL, 5, NULL);
}