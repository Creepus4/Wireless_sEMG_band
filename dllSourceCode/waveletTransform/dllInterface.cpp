#include "waveletTransform.h"

extern "C" {
	static WaveletTransform* waveletTransform = nullptr;

	__declspec(dllexport) void createWaveletObjArray(const float* frequencyArray, const uint32_t frequencyArraySize, const uint32_t dataSize, const uint32_t samplingFreq) {
		delete waveletTransform;
		waveletTransform = new WaveletTransform(frequencyArray, frequencyArraySize, dataSize, samplingFreq);
	}

	__declspec(dllexport) void deleteWaveletObj() {
		delete waveletTransform;
		waveletTransform = nullptr;
	}

	__declspec(dllexport) void transform(float* output, const uint8_t index) {
		waveletTransform->writeTransform(output, index);
	}

	__declspec(dllexport) void pushData(const float data, const uint8_t index) {
		waveletTransform->push(data, index);
	}
}
