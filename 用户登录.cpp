#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <stdlib.h>
#include <ctype.h>

// 跨平台相关头文件（区分Windows/Linux/Mac）
#if defined(_WIN32) || defined(_WIN64)
#include <conio.h>       // Windows下隐藏密码用
#include <windows.h>     // 设置控制台编码为GBK（支持中文）
#else
#include <termios.h>     // Linux/Mac下隐藏密码用
#include <unistd.h>
#include <locale.h>      // Linux/Mac下设置UTF-8编码
#endif

// 常量定义（适配中文和加密需求）
#define USERNAME_MAX 40        // 用户名最大字节数（中文最多20个，GBK编码）
#define PASSWORD_MAX 16        // 密码最大长度（1-15字符）
#define SHA1_LEN 41            // SHA-1哈希值字符串长度（40位+结束符）
#define DATA_FILE "users.txt"  // 存储用户数据的文件

// ====================== SHA-1加密实现（无需额外库）======================
typedef struct {
    unsigned int h[5];          // SHA-1哈希缓冲区
    unsigned int length[2];     // 消息长度（bit）
    unsigned char buffer[64];   // 消息块缓冲区
} SHA1_CTX;

// 循环左移n位
static unsigned int SHA1_ROL(unsigned int value, int n) {
    return (value << n) | (value >> (32 - n));
}

// 初始化SHA-1上下文
static void SHA1_Init(SHA1_CTX* ctx) {
    ctx->h[0] = 0x67452301;
    ctx->h[1] = 0xEFCDAB89;
    ctx->h[2] = 0x98BADCFE;
    ctx->h[3] = 0x10325476;
    ctx->h[4] = 0xC3D2E1F0;
    ctx->length[0] = ctx->length[1] = 0;
}

// 处理512位消息块
static void SHA1_Transform(SHA1_CTX* ctx) {
    unsigned int w[80], a, b, c, d, e, temp;
    int i;

    // 扩展64字节消息块到80字
    for (i = 0; i < 16; i++) {
        w[i] = (ctx->buffer[i * 4] << 24) | (ctx->buffer[i * 4 + 1] << 16) |
            (ctx->buffer[i * 4 + 2] << 8) | ctx->buffer[i * 4 + 3];
    }
    for (; i < 80; i++) {
        w[i] = SHA1_ROL(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1);
    }

    a = ctx->h[0];
    b = ctx->h[1];
    c = ctx->h[2];
    d = ctx->h[3];
    e = ctx->h[4];

    // 4轮哈希运算
    for (i = 0; i < 20; i++) {
        temp = SHA1_ROL(a, 5) + ((b & c) | (~b & d)) + e + w[i] + 0x5A827999;
        e = d; d = c; c = SHA1_ROL(b, 30); b = a; a = temp;
    }
    for (; i < 40; i++) {
        temp = SHA1_ROL(a, 5) + (b ^ c ^ d) + e + w[i] + 0x6ED9EBA1;
        e = d; d = c; c = SHA1_ROL(b, 30); b = a; a = temp;
    }
    for (; i < 60; i++) {
        temp = SHA1_ROL(a, 5) + ((b & c) | (b & d) | (c & d)) + e + w[i] + 0x8F1BBCDC;
        e = d; d = c; c = SHA1_ROL(b, 30); b = a; a = temp;
    }
    for (; i < 80; i++) {
        temp = SHA1_ROL(a, 5) + (b ^ c ^ d) + e + w[i] + 0xCA62C1D6;
        e = d; d = c; c = SHA1_ROL(b, 30); b = a; a = temp;
    }

    ctx->h[0] += a;
    ctx->h[1] += b;
    ctx->h[2] += c;
    ctx->h[3] += d;
    ctx->h[4] += e;
}

// 更新SHA-1上下文（输入消息）- 修复size_t转unsigned int警告
static void SHA1_Update(SHA1_CTX* ctx, const unsigned char* data, size_t len) {
    size_t i = 0, j;  // 变量类型改为size_t，匹配len的类型

    // 计算消息总长度（bit）
    j = (ctx->length[0] >> 3) & 0x3F;
    if ((ctx->length[0] += (unsigned int)(len << 3)) < (unsigned int)(len << 3)) {  // 显式转换
        ctx->length[1]++;
    }
    ctx->length[1] += (unsigned int)(len >> 29);  // 显式转换

    // 填充消息块
    if ((j + len) > 63) {
        memcpy(&ctx->buffer[j], data, 64 - j);
        SHA1_Transform(ctx);
        for (i = 64 - j; i + 63 < len; i += 64) {
            memcpy(ctx->buffer, &data[i], 64);
            SHA1_Transform(ctx);
        }
        j = 0;
    }
    else {
        i = 0;
    }
    memcpy(&ctx->buffer[j], &data[i], len - i);
}

// 完成哈希计算，输出40位十六进制字符串- 修复sprintf不安全警告
static void SHA1_Final(unsigned char* digest, SHA1_CTX* ctx) {
    size_t i, j;  // 变量类型改为size_t
    unsigned char padding[64] = { 0x80 };

    // 填充消息（满足长度模512=448）
    i = (ctx->length[0] >> 3) & 0x3F;
    SHA1_Update(ctx, padding, (i < 56) ? (56 - i) : (120 - i));

    // 追加消息长度（64位）
    for (j = 0; j < 4; j++) {
        ctx->buffer[56 + j] = (ctx->length[0] >> (24 - j * 8)) & 0xFF;
        ctx->buffer[60 + j] = (ctx->length[1] >> (24 - j * 8)) & 0xFF;
    }
    SHA1_Transform(ctx);

    // 转换为十六进制字符串- 用sprintf_s替换sprintf，避免不安全警告
    for (i = 0; i < 5; i++) {
        sprintf_s((char*)&digest[i * 8], 9, "%08X", ctx->h[i]);  // 9=8位字符+结束符
    }
    digest[40] = '\0';  // 确保字符串终止符
}

// 密码加密函数：输入密码，输出SHA-1哈希字符串- 修复strcpy不安全警告
void encryptPassword(const char* password, char* encrypted) {
    SHA1_CTX ctx;
    unsigned char digest[SHA1_LEN];
    SHA1_Init(&ctx);
    SHA1_Update(&ctx, (const unsigned char*)password, strlen(password));
    SHA1_Final(digest, &ctx);
    strcpy_s(encrypted, SHA1_LEN, (char*)digest);  // 用strcpy_s替换strcpy
}

// ====================== 跨平台隐藏密码输入（不回显）======================
#if defined(_WIN32) || defined(_WIN64)
// Windows系统：用conio.h的_getch()实现（修复getch废弃警告）
void inputPassword(char* password) {
    size_t i = 0;  // 变量类型改为size_t，匹配PASSWORD_MAX
    char ch;
    printf("请输入密码（不超过%d字符）：", PASSWORD_MAX - 1);
    while ((ch = _getch()) != '\r') {  // 替换getch()为_getch()
        if (ch == '\b' && i > 0) {    // 支持退格
            i--;
            printf("\b \b");          // 清除屏幕上的*
        }
        else if (i < PASSWORD_MAX - 1 && isprint((unsigned char)ch)) {  // 显式转换避免警告
            password[i++] = ch;
            printf("*");              // 显示星号代替密码
        }
    }
    password[i] = '\0';  // 手动添加字符串结束符
    printf("\n");
}

// 设置Windows控制台编码为GBK（支持中文输入）
void setConsoleGBK() {
    SetConsoleOutputCP(936);  // 输出编码GBK
    SetConsoleCP(936);        // 输入编码GBK
}
#else
// Linux/Mac系统：修改终端属性实现密码隐藏
void setTerminalEcho(bool enable) {
    struct termios term;
    tcgetattr(STDIN_FILENO, &term);
    if (enable) {
        term.c_lflag |= ECHO;  // 启用回显
    }
    else {
        term.c_lflag &= ~ECHO; // 禁用回显
    }
    tcsetattr(STDIN_FILENO, TCSANOW, &term);
}

void inputPassword(char* password) {
    size_t i = 0;  // 变量类型改为size_t
    char ch;
    printf("请输入密码（不超过%d字符）：", PASSWORD_MAX - 1);
    setTerminalEcho(false);  // 禁用回显
    while ((ch = getchar()) != '\n' && ch != EOF) {  // 按回车结束
        if (ch == '\b' && i > 0) {                  // 支持退格
            i--;
            printf("\b \b");
        }
        else if (i < PASSWORD_MAX - 1 && isprint((unsigned char)ch)) {
            password[i++] = ch;
            printf("*");
        }
    }
    password[i] = '\0';
    setTerminalEcho(true);  // 恢复回显
    printf("\n");
}

// 设置Linux/Mac终端编码为UTF-8（支持中文）
void setConsoleUTF8() {
    setlocale(LC_ALL, "zh_CN.UTF-8");
}
#endif

// ====================== 中文用户名输入（支持空格）======================
void inputUsername(char* username, const char* prompt) {
    printf("%s（不超过%d字符，支持中文和空格）：", prompt, (USERNAME_MAX - 1) / 2);
    // 用fgets读取整行（支持中文和空格）
    fgets(username, USERNAME_MAX, stdin);
    // 去掉fgets读取的换行符（\n）- 修复size_t转int警告
    size_t len = strlen(username);  // 变量类型改为size_t
    if (len > 0 && username[len - 1] == '\n') {
        username[len - 1] = '\0';
    }
    // 去除首尾空格
    char* start = username;
    while (*start && isspace((unsigned char)*start)) start++;
    char* end = username + strlen(username) - 1;
    while (end > start && isspace((unsigned char)*end)) end--;
    *(end + 1) = '\0';
    strcpy_s(username, USERNAME_MAX, start);  // 用strcpy_s替换strcpy
}

// ====================== 核心功能：注册和登录 ======================
// 注册函数：支持中文用户名、密码加密存储
void userRegister() {
    char username[USERNAME_MAX];
    char password[PASSWORD_MAX];
    char encryptedPwd[SHA1_LEN];
    char tempUser[USERNAME_MAX];
    char tempPwd[SHA1_LEN] = { 0 };  // 初始化，确保零终止符（修复警告）
    FILE* fp = NULL;
    bool isExist = false;

    printf("\n===== 用户注册 =====\n");
    // 清除scanf残留的\n- 修复getchar返回值被忽略警告
    (void)getchar();  // 强制忽略返回值

    inputUsername(username, "请输入用户名");

    // 用户名非空校验
    if (strlen(username) == 0) {
        printf("错误：用户名不能为空！注册失败！\n");
        return;
    }

    // 输入隐藏密码
    inputPassword(password);
    // 密码非空校验
    if (strlen(password) == 0) {
        printf("错误：密码不能为空！注册失败！\n");
        return;
    }

    // 检查用户名是否已存在
    fp = fopen(DATA_FILE, "r");
    if (fp != NULL) {
        // 读取文件：中文用户名+空格+加密密码（每行一个用户）
        while (fgets(tempUser, USERNAME_MAX, fp) != NULL) {
            // 去掉tempUser中的换行符- 修复size_t转int警告
            size_t len = strlen(tempUser);  // 变量类型改为size_t
            if (len > 0 && tempUser[len - 1] == '\n') {
                tempUser[len - 1] = '\0';
            }
            // 读取对应的加密密码（跳过空格）
            if (fscanf_s(fp, " %s\n", tempPwd, (unsigned)_countof(tempPwd)) == 1) {  // 用fscanf_s替换fscanf，指定缓冲区大小
                if (strcmp(username, tempUser) == 0) {
                    isExist = true;
                    break;
                }
            }
        }
        fclose(fp);
    }

    if (isExist) {
        printf("错误：用户名已存在！注册失败！\n");
        return;
    }

    // 密码加密
    encryptPassword(password, encryptedPwd);

    // 写入文件（追加模式）
    fp = fopen(DATA_FILE, "a");
    if (fp == NULL) {
        printf("错误：文件打开失败！注册失败！\n");
        return;
    }
    // 存储格式：中文用户名\n 加密密码\n（避免中文含空格导致解析错误）
    fprintf(fp, "%s\n%s\n", username, encryptedPwd);
    fclose(fp);
    printf("恭喜！注册成功！\n");
}

// 登录函数：中文用户名匹配+加密密码校验
bool userLogin() {
    char username[USERNAME_MAX];
    char password[PASSWORD_MAX];
    char encryptedPwd[SHA1_LEN];
    char tempUser[USERNAME_MAX];
    char tempPwd[SHA1_LEN] = { 0 };  // 初始化，确保零终止符（修复警告）
    FILE* fp = NULL;

    printf("\n===== 用户登录 =====\n");
    // 清除scanf残留的\n- 修复getchar返回值被忽略警告
    (void)getchar();  // 强制忽略返回值

    inputUsername(username, "请输入用户名");

    // 输入隐藏密码
    inputPassword(password);

    // 打开用户数据文件
    fp = fopen(DATA_FILE, "r");
    if (fp == NULL) {
        printf("错误：无注册用户！登录失败！\n");
        return false;
    }

    // 循环查找匹配用户
    while (fgets(tempUser, USERNAME_MAX, fp) != NULL) {
        // 去掉换行符- 修复size_t转int警告
        size_t len = strlen(tempUser);  // 变量类型改为size_t
        if (len > 0 && tempUser[len - 1] == '\n') {
            tempUser[len - 1] = '\0';
        }
        // 读取加密密码- 用fscanf_s替换fscanf，指定缓冲区大小
        if (fscanf_s(fp, " %s\n", tempPwd, (unsigned)_countof(tempPwd)) != 1) {
            continue;  // 格式错误，跳过该用户
        }
        // 用户名匹配，校验密码
        if (strcmp(username, tempUser) == 0) {
            encryptPassword(password, encryptedPwd);
            fclose(fp);
            return strcmp(encryptedPwd, tempPwd) == 0;
        }
    }

    fclose(fp);
    return false;
}

// ====================== 主函数（菜单交互）======================
int main() {
    int choice;

    // 设置控制台编码（支持中文）
#if defined(_WIN32) || defined(_WIN64)
    setConsoleGBK();
#else
    setConsoleUTF8();
#endif

    printf("==================== C语言用户登录系统 ====================\n");
    printf("说明：支持中文用户名（含空格），密码SHA-1加密存储，输入不回显\n");

    // 循环菜单
    while (1) {
        printf("\n请选择功能：\n");
        printf("1. 新用户注册\n");
        printf("2. 已有用户登录\n");
        printf("3. 退出系统\n");
        printf("==========================================================\n");
        printf("请输入选项（1-3）：");
        if (scanf_s("%d", &choice) != 1) {  // 用scanf_s替换scanf，避免不安全警告
            // 处理非数字输入- 修复getchar返回值被忽略警告
            while (getchar() != '\n') (void)0;  // 清空输入缓冲区，强制忽略返回值
            choice = 0;
        }

        switch (choice) {
        case 1:
            userRegister();
            break;
        case 2:
            if (userLogin()) {
                printf("登录成功！欢迎使用系统！\n");
            }
            else {
                printf("登录失败！用户名或密码错误！\n");
            }
            break;
        case 3:
            printf("\n感谢使用，再见！\n");
            return 0;
        default:
            printf("错误：输入无效！请输入1-3之间的数字！\n");
        }
    }
}
