/**
 * I2S Audio Capture Module
 * Handles continuous audio capture from I2S microphone
 */
#ifndef I2S_AUDIO_H
#define I2S_AUDIO_H

#include <stdint.h>
#include <stddef.h>
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "config.h"

// Audio frame structure
typedef struct {
    int16_t *samples;           // Audio samples (16-bit PCM)
    size_t sample_count;        // Number of samples in frame
    uint32_t timestamp_ms;      // Capture timestamp
    uint32_t sequence_number;   // Frame sequence counter
} AudioFrame;

// Audio statistics
typedef struct {
    uint32_t frames_captured;
    uint32_t buffer_overruns;
    uint32_t i2s_read_errors;
    float peak_amplitude;
    float rms_level_db;
} AudioStats;

class I2SAudio {
public:
    I2SAudio();
    ~I2SAudio();
    
    // Initialize I2S peripheral
    bool init();
    
    // Start/Stop audio capture
    bool start();
    bool stop();
    bool isRunning();
    
    // Get audio frame (blocking with timeout)
    bool getFrame(AudioFrame *frame, uint32_t timeout_ms);
    
    // Release frame buffer back to pool
    void releaseFrame(AudioFrame *frame);
    
    // Configuration
    void setSampleRate(uint32_t sample_rate);
    uint32_t getSampleRate();
    void setGain(float gain);
    float getGain();
    
    // Statistics
    AudioStats getStats();
    void resetStats();
    
private:
    static void audioTaskWrapper(void *param);
    void audioTask();
    
    bool initialized_;
    bool running_;
    uint32_t sample_rate_;
    uint32_t sequence_counter_;
    TaskHandle_t audio_task_handle_;
    SemaphoreHandle_t config_mutex_;
    float audio_gain_;
    
    QueueHandle_t frame_queue_;
    AudioFrame *frame_pool_[AUDIO_BUFFER_COUNT];
    AudioStats stats_;
};

// Global instance
extern I2SAudio g_audio;

#endif // I2S_AUDIO_H
