idf_component_register(
    SRCS 
        "main.cpp"
        "i2s_audio.cpp"
        "mqtt_handler.cpp"
        "policy_handler.cpp"
    INCLUDE_DIRS "."
    REQUIRES 
        nvs_flash 
        esp_wifi 
        mqtt 
        json
        esp_http_server
        driver
)
