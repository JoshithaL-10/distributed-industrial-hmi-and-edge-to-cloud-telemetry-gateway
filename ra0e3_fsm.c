#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#endif

#define SERVER_IP "127.0.0.1"
#define SERVER_PORT 5000

typedef struct __attribute__((packed)) {
    uint8_t event_status;
    uint8_t pad_x;
    uint8_t pad_y;
    uint8_t als_msb;
    uint8_t als_lsb;
    uint8_t checksum;
} PSoC_Packet_t;

typedef enum {
    STATE_LOCKED,
    STATE_CREDENTIAL_ENTRY,
    STATE_ACCESS_GRANTED,
    STATE_TAMPER_ALERT
} AccessState_t;

static AccessState_t current_state = STATE_LOCKED;
static uint16_t entered_pin = 0;
static const uint16_t MASTER_PIN = 12;

bool ValidateChecksum(const PSoC_Packet_t *pkt) {
    uint8_t expected = pkt->event_status ^ pkt->pad_x ^ pkt->pad_y ^ pkt->als_msb ^ pkt->als_lsb;
    return (expected == pkt->checksum);
}

void ProcessStateMachine(const PSoC_Packet_t *pkt, char *out_json, size_t json_size) {
    uint16_t als_lux = ((uint16_t)pkt->als_msb << 8) | pkt->als_lsb;
    const char *state_str = "LOCKED";

    switch (current_state) {
        case STATE_LOCKED:
            if (pkt->event_status & 0x01) {
                current_state = STATE_CREDENTIAL_ENTRY;
                state_str = "PIN_ENTRY_MODE";
            }
            break;
        case STATE_CREDENTIAL_ENTRY:
            if (pkt->event_status & 0x02) {
                entered_pin = (entered_pin * 10) + 1;
                state_str = "DIGIT_1_RECORDED";
            } else if (pkt->event_status & 0x04) {
                entered_pin = (entered_pin * 10) + 2;
                state_str = "DIGIT_2_RECORDED";
            } else if (pkt->event_status & 0x08) {
                if (entered_pin == MASTER_PIN) {
                    current_state = STATE_ACCESS_GRANTED;
                    state_str = "ACCESS_GRANTED_UNLOCKED";
                } else {
                    current_state = STATE_LOCKED;
                    entered_pin = 0;
                    state_str = "AUTH_FAILED_LOCKED";
                }
            }
            break;
        case STATE_ACCESS_GRANTED:
            state_str = "UNLOCKED";
            break;
        case STATE_TAMPER_ALERT:
            state_str = "TAMPER_LOCK";
            break;
    }

    snprintf(out_json, json_size,
             "{\"src\":\"RA0E3_SIL\",\"fsm\":\"%s\",\"evt\":%u,\"x\":%u,\"y\":%u,\"lux\":%u}",
             state_str, pkt->event_status, pkt->pad_x, pkt->pad_y, als_lux);
}

int main(void) {
    printf("===================================================================\n");
    printf("  [Renesas RA0E3 Host Controller] Initializing SIL FSM Engine...\n");
    printf("===================================================================\n\n");

#ifdef _WIN32
    WSADATA wsa;
    WSAStartup(MAKEWORD(2, 2), &wsa);
#endif

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        perror("[Error] Socket creation failed");
        return 1;
    }

    struct sockaddr_in serv_addr;
    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(SERVER_PORT);
    inet_pton(AF_INET, SERVER_IP, &serv_addr.sin_addr);

    printf("[RA0E3 Host] Connecting to PSoC 4100T Virtual I2C bus at %s:%d...\n", SERVER_IP, SERVER_PORT);

    while (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("[RA0E3 Host] Waiting for virtual sensor server to come online...\n");
#ifdef _WIN32
        Sleep(1000);
#else
        sleep(1);
#endif
    }

    printf("[RA0E3 Host] I2C Bus Link Active. Listening for sensor events...\n\n");

    PSoC_Packet_t packet;
    char json_buffer[256];

    while (1) {
        int bytes_read = recv(sock, (char *)&packet, sizeof(PSoC_Packet_t), 0);
        if (bytes_read <= 0) {
            printf("[RA0E3 Host] Virtual I2C bus closed. Exiting.\n");
            break;
        }

        if (bytes_read == sizeof(PSoC_Packet_t)) {
            if (ValidateChecksum(&packet)) {
                ProcessStateMachine(&packet, json_buffer, sizeof(json_buffer));
                printf("[I2C Read PASS] Checksum Verified: 0x%02X\n", packet.checksum);
                printf("                -> State Machine Output: %s\n\n", json_buffer);
            } else {
                printf("[I2C Read FAIL] Checksum mismatch! Corrupted packet rejected (0x%02X)\n\n", packet.checksum);
            }
        }
    }

#ifdef _WIN32
    closesocket(sock);
    WSACleanup();
#else
    close(sock);
#endif

    return 0;
}