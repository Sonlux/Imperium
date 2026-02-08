/**
 * Policy Handler Module
 * Processes control messages from Imperium IBN framework
 */
#ifndef POLICY_HANDLER_H
#define POLICY_HANDLER_H

#include <stdint.h>

class PolicyHandler {
public:
    PolicyHandler();
    
    // Process incoming control message
    void processControlMessage(const char* data, int len);
    
    // Get current policy state
    int getQoS() { return current_qos_; }
    uint32_t getSampleRate() { return current_sample_rate_; }
    bool isEnabled() { return enabled_; }
    uint32_t getPublishInterval() { return publish_interval_ms_; }
    float getAudioGain() { return audio_gain_; }
    
private:
    void handleSetQoS(int qos);
    void handleSetSampleRate(uint32_t sample_rate);
    void handleEnable();
    void handleDisable();
    void handleReset();
    void handleSetPublishInterval(uint32_t interval_ms);
    void handleSetAudioGain(float gain);
    
    int current_qos_;
    uint32_t current_sample_rate_;
    bool enabled_;
    uint32_t publish_interval_ms_;
    float audio_gain_;
};

// Global instance
extern PolicyHandler g_policy;

#endif // POLICY_HANDLER_H
