#include "fileReader.h"
#include <iostream>

extern "C" {
	__declspec(dllexport) void writeFile(const char* filename, const uint16_t* data, uint32_t length){
		std::vector<uint16_t> vec(data, data + length);
		FileReader::writeData(filename, vec);
	}
	__declspec(dllexport) uint16_t* readFile(const char* filename, uint32_t* length) {
		std::vector<uint16_t> vec;
		vec = FileReader::readData(filename);

		*length = vec.size();
		uint16_t* buffer = new uint16_t[*length];

		std::memcpy(buffer, vec.data(), *length * sizeof(uint16_t));
		return buffer;
	}

	__declspec(dllexport) void freeBuffer(uint16_t* ptr) {
		delete[] ptr;
	}
}
