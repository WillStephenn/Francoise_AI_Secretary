#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

// Conditional includes for sockets
#ifdef _WIN32
#include <winsock2.h>
#pragma comment(lib, "ws2_32.lib")
#else // POSIX systems
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h> // For close()
#endif

#define MAX_RMS_FOR_BAR 0.4f
#define BAR_WIDTH 40
#define PITCH_MIN_HZ 100.0f // Added
#define PITCH_MAX_HZ 1000.0f // Added
// BAR_CHAR: On some systems, you might need to use wide characters (wchar_t) 
// and functions like wprintf/putwc for '█' to display correctly.
// Ensure your terminal is configured for UTF-8.
#define BAR_CHAR '.' 
#define PORT 12345 // Example port, ensure it matches the Python client

void clear_terminal() {
#ifdef _WIN32
    system("cls");
#else
    system("clear");
#endif
}

void render_audio(float rms_value, int pitch_value) { // Modified
    clear_terminal();
    printf("---YOU ARE NOW CONNECTED TO FRANÇOISE---\n");

    // RMS Bar
    float scaled_rms = fminf(fmaxf(rms_value, 0.0f), MAX_RMS_FOR_BAR) / MAX_RMS_FOR_BAR;
    int rms_bar_length = (int)(scaled_rms * BAR_WIDTH);
    printf("RMS  : ");
    for (int i = 0; i < rms_bar_length; i++) {
        putchar(BAR_CHAR);
    }
    for (int i = 0; i < (BAR_WIDTH - rms_bar_length); i++) {
        putchar(' ');
    }
    printf("\n");

    // Pitch Bar
    float scaled_pitch = 0.0f;
    if (pitch_value > 0) { // Only scale if pitch is detected
        scaled_pitch = fminf(fmaxf((float)pitch_value, PITCH_MIN_HZ), PITCH_MAX_HZ);
        scaled_pitch = (scaled_pitch - PITCH_MIN_HZ) / (PITCH_MAX_HZ - PITCH_MIN_HZ);
    }
    int pitch_bar_length = (int)(scaled_pitch * BAR_WIDTH);
    printf("Pitch: ");
    for (int i = 0; i < pitch_bar_length; i++) {
        putchar(BAR_CHAR);
    }
    for (int i = 0; i < (BAR_WIDTH - pitch_bar_length); i++) {
        putchar(' ');
    }
    printf(" %d Hz\n", pitch_value > 0 ? pitch_value : 0);

    // Footer
    for (int i = 0; i < BAR_WIDTH + 7; i++) { // Adjusted width for labels
        putchar('-');
    }
    printf("\n");
    fflush(stdout); // Ensure output is displayed immediately
}

int main() {
    printf("C Visualiser starting...\n");

    // --- IPC Setup (Example: UDP Server) ---
#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        perror("WSAStartup failed");
        return 1;
    }
#endif

    int sockfd;
    struct sockaddr_in servaddr, cliaddr;
    char buffer[1024];
    socklen_t len = sizeof(cliaddr);

    // Creating socket file descriptor
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket creation failed");
        exit(EXIT_FAILURE);
    }

    memset(&servaddr, 0, sizeof(servaddr));
    memset(&cliaddr, 0, sizeof(cliaddr));

    // Filling server information
    servaddr.sin_family = AF_INET; // IPv4
    servaddr.sin_addr.s_addr = INADDR_ANY;
    servaddr.sin_port = htons(PORT);

    // Bind the socket with the server address
    if (bind(sockfd, (const struct sockaddr *)&servaddr, sizeof(servaddr)) < 0) {
        perror("bind failed");
        close(sockfd); // Ensure socket is closed on failure
        exit(EXIT_FAILURE);
    }

    printf("C Visualiser listening on port %d\n", PORT);

    while (1) {
        ssize_t n = recvfrom(sockfd, (char *)buffer, sizeof(buffer) -1,
                         0, (struct sockaddr *) &cliaddr, // MSG_WAITALL might not be ideal for UDP, using 0
                         &len);
        if (n > 0) {
            buffer[n] = '\0';
            float rms_value = 0.0f;
            int pitch_value = 0;
            // Expecting data in format "rms,pitch"
            char* token = strtok(buffer, ",");
            if (token != NULL) {
                rms_value = atof(token);
                token = strtok(NULL, ",");
                if (token != NULL) {
                    pitch_value = atoi(token);
                }
            }
            render_audio(rms_value, pitch_value); // Modified
        } else if (n < 0) {
            perror("recvfrom error");
            // Potentially break or handle error
        }
        // Add a small delay if messages are too rapid and overwhelm terminal
        // usleep(10000); // 10ms, requires unistd.h
    }

    close(sockfd);
#ifdef _WIN32
    WSACleanup();
#endif

    // Fallback for testing rendering without IPC:
    // printf("IPC code is commented out. Displaying test pattern.\\n");
    // render_audio(0.0f);
    // Simulate receiving some data if not using sockets for testing:
    // float test_rms[] = {0.05f, 0.1f, 0.2f, 0.3f, 0.4f, 0.3f, 0.2f, 0.1f, 0.05f, 0.0f};
    // int test_pitch[] = {0, 120, 150, 200, 250, 200, 150, 120, 0, 0};
    // for (int i=0; i<10; ++i) {
    //     render_audio(test_rms[i], test_pitch[i]);
    //     #ifdef _WIN32
    //         Sleep(200); // milliseconds
    //     #else
    //         usleep(200000); // microseconds
    //     #endif
    // }
    
    return 0;
}
