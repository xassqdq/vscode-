#define _CRT_SECURE_NO_WARNINGS


#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// 宏定义棋盘的行和列（井字棋为3x3）
#define ROW 3
#define COL 3

// 函数声明
// 初始化棋盘
void InitBoard(char board[ROW][COL], int row, int col);
// 打印棋盘
void DisplayBoard(char board[ROW][COL], int row, int col);
// 玩家落子
void PlayerMove(char board[ROW][COL], int row, int col);
// 电脑落子
void ComputerMove(char board[ROW][COL], int row, int col);
// 判断游戏结果：玩家赢('*')、电脑赢('#')、平局('Q')、继续('C')
char IsWin(char board[ROW][COL], int row, int col);
// 判断棋盘是否已满（用于判断平局）
int IsFull(char board[ROW][COL], int row, int col);

int main() {
    // 定义3x3的棋盘数组，存储棋子（空格/玩家* /电脑#）
    char board[ROW][COL];
    char result = 'C'; // 游戏结果初始化为继续

    // 设置随机数种子（用于电脑落子的随机位置）
    srand((unsigned int)time(NULL));

    // 初始化棋盘
    InitBoard(board, ROW, COL);

    // 游戏主循环
    while (result == 'C') {
        // 打印棋盘
        DisplayBoard(board, ROW, COL);
        // 玩家落子
        PlayerMove(board, ROW, COL);
        // 判断玩家落子后是否获胜/平局
        result = IsWin(board, ROW, COL);
        if (result != 'C') {
            break;
        }
        // 电脑落子
        ComputerMove(board, ROW, COL);
        // 判断电脑落子后是否获胜/平局
        result = IsWin(board, ROW, COL);
        if (result != 'C') {
            break;
        }
    }

    // 打印最终棋盘
    DisplayBoard(board, ROW, COL);
    // 根据结果输出提示
    if (result == '*') {
        printf("恭喜你，你赢了！\n");
    }
    else if (result == '#') {
        printf("很遗憾，电脑赢了！\n");
    }
    else if (result == 'Q') {
        printf("棋盘下满了，平局！\n");
    }

    return 0;
}

// 初始化棋盘：将所有位置设为空格
void InitBoard(char board[ROW][COL], int row, int col) {
    for (int i = 0; i < row; i++) {
        for (int j = 0; j < col; j++) {
            board[i][j] = ' ';
        }
    }
}

// 打印棋盘：格式化输出，增强视觉效果
void DisplayBoard(char board[ROW][COL], int row, int col) {
    for (int i = 0; i < row; i++) {
        // 打印棋子行（如：  * |  # |    ）
        for (int j = 0; j < col; j++) {
            printf(" %c ", board[i][j]);
            if (j < col - 1) {
                printf("|");
            }
        }
        printf("\n");
        // 打印分隔线（如：---+---+---），最后一行不打印
        if (i < row - 1) {
            for (int j = 0; j < col; j++) {
                printf("---");
                if (j < col - 1) {
                    printf("+");
                }
            }
            printf("\n");
        }
    }
}

// 玩家落子：输入行和列，验证合法性后落子（玩家用*）
void PlayerMove(char board[ROW][COL], int row, int col) {
    int x = 0, y = 0;
    printf("你的回合，请输入落子的行和列（如：1 2 表示第1行第2列）：\n");

    while (1) {
        // 接收玩家输入的行和列（玩家习惯从1开始，数组下标从0开始）
        scanf("%d %d", &x, &y);
        // 验证输入的行和列是否在合法范围（1-3）
        if (x >= 1 && x <= row && y >= 1 && y <= col) {
            // 验证该位置是否为空
            if (board[x - 1][y - 1] == ' ') {
                board[x - 1][y - 1] = '*'; // 玩家落子为*
                break;
            }
            else {
                printf("该位置已有棋子，请重新输入！\n");
            }
        }
        else {
            printf("输入非法，请输入1-%d之间的行和列！\n", row);
        }
    }
}

// 电脑落子：随机生成合法位置，落子为#
void ComputerMove(char board[ROW][COL], int row, int col) {
    int x = 0, y = 0;
    printf("电脑的回合：\n");

    while (1) {
        // 生成1-3的随机行和列（转换为数组下标0-2）
        x = rand() % row;
        y = rand() % col;
        // 验证该位置是否为空
        if (board[x][y] == ' ') {
            board[x][y] = '#'; // 电脑落子为#
            break;
        }
    }
}

// 判断棋盘是否已满：满则返回1，未满返回0
int IsFull(char board[ROW][COL], int row, int col) {
    for (int i = 0; i < row; i++) {
        for (int j = 0; j < col; j++) {
            if (board[i][j] == ' ') {
                return 0; // 还有空格，棋盘未满
            }
        }
    }
    return 1; // 棋盘已满
}

// 判断游戏结果
char IsWin(char board[ROW][COL], int row, int col) {
    // 1. 判断行是否连成线
    for (int i = 0; i < row; i++) {
        if (board[i][0] == board[i][1] && board[i][1] == board[i][2] && board[i][0] != ' ') {
            return board[i][0]; // 返回获胜方的棋子（*或#）
        }
    }

    // 2. 判断列是否连成线
    for (int j = 0; j < col; j++) {
        if (board[0][j] == board[1][j] && board[1][j] == board[2][j] && board[0][j] != ' ') {
            return board[0][j];
        }
    }

    // 3. 判断两条对角线是否连成线
    if (board[0][0] == board[1][1] && board[1][1] == board[2][2] && board[0][0] != ' ') {
        return board[0][0];
    }
    if (board[0][2] == board[1][1] && board[1][1] == board[2][0] && board[0][2] != ' ') {
        return board[0][2];
    }

    // 4. 判断是否平局（棋盘满且未分胜负）
    if (IsFull(board, row, col) == 1) {
        return 'Q';
    }

    // 5. 游戏继续
    return 'C';
}