#pragma once
#include <vector>
#include <fstream>
#include <string>
#include <stdexcept>


class FileReader {
	public:

	static std::vector<uint16_t> readData(const std::string& filename) {
		std::ifstream file(filename, std::ios::binary | std::ios::ate);

		std::streamsize size = file.tellg();
		file.seekg(0, std::ios::beg);
		std::vector<uint8_t> packedData(size);

		file.read(reinterpret_cast<char*>(packedData.data()), size);
		std::vector<uint16_t> data = unpack12bit(packedData);

		file.close();
		return data;
	}

	static void writeData(const std::string& filename, const std::vector<uint16_t>& data) {
		std::ofstream file(filename, std::ios::binary);
		
		std::vector<uint8_t> packedData = pack12bit(data);
		file.write(reinterpret_cast<const char*>(packedData.data()), packedData.size());
		
		file.close();
	}
	
	private:

	static std::vector<uint8_t> pack12bit(const std::vector<uint16_t>& data) {
		std::vector<uint8_t> packedData;
		packedData.reserve((data.size() * 12 + 7) / 8);

		uint32_t buffer = 0;
		uint8_t bitsInBuffer = 0;

		for (uint16_t d : data) {
			buffer |= (uint32_t(d) << bitsInBuffer);
			bitsInBuffer += 12;

			while (bitsInBuffer >= 8) {
				packedData.push_back(static_cast<uint8_t>(buffer & 0xFF));
				buffer >>= 8;
				bitsInBuffer -= 8;
				}
			}

		if (bitsInBuffer > 0) {
			packedData.push_back(static_cast<uint8_t>(buffer & 0xFF));
		}

		return packedData;
	}
	
	static std::vector<uint16_t> unpack12bit(const std::vector<uint8_t>& packedData) {

		std::vector<uint16_t> data;
		data.reserve(packedData.size() * 8 / 12);
    
		uint32_t buffer = 0;
		uint8_t bitsInBuffer = 0;

		for (uint8_t byte : packedData) {
			buffer |= (uint32_t(byte) << bitsInBuffer);
			bitsInBuffer += 8;

			while (bitsInBuffer >= 12) {
				uint16_t sample = buffer & 0xFFF;
				data.push_back(sample);

				buffer >>= 12;
				bitsInBuffer -= 12;
			}
		}
		return data;
	}
};
