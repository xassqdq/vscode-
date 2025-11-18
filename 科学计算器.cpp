//头文件引入（第一部分）

#define _CRT_SECURE_NO_WARNINGS
#include<stdio.h>
#include <stdlib.h>
#include <math.h>
#include <ctype.h>
#include <string.h>
#include <stdbool.h>

//宏定义与全局变量（第二部分）

// 数学常量定义（高精度）
#define PI 3.14159265358979323846
#define E 2.71828182845904523536
// 全局配置：控制三角函数的角度模式（弧度/角度）整个程序中共享的模式标记，三角函数（如sine）和反三角函数（如arcsine）会根据它判断是否需要角度 / 弧度转换。
int useRadians = 1;  // 1=弧度模式，0=角度模式（初始为弧度）

//函数声明（第三部分）
void displayMenu();
double add(double a, double b);//加法
double subtract(double a, double b);//减法
double multiply(double a, double b);//乘法
double divide(double a, double b);//除法
double power(double base, double exponent);//幂运算
double squareRoot(double num);
double nthRoot(double num, double n);
double factorial(int n);
double sine(double angle, int isRadians);
double cosine(double angle, int isRadians);
double tangent(double angle, int isRadians);
double arcsine(double value);
double arccosine(double value);
double arctangent(double value);
double logarithm(double num, double base);
double naturalLog(double num);
int isValidInput();
double parseMathInput(char* input); // 新增：解析数学输入的函数



//核心函数实现（第四部分）

//1.基础运算
double add(double a, double b)
{
	return a + b;
}//加法
double subtract(double a, double b)
{
	return a - b;
}//减法
double multiply(double a, double b)
{
	return a * b;
}//乘法
double divide(double a, double b)
{
	if (b == 0)
	{
		printf("错误！除数不能为0！\n");
		return 0;
	}
	return a + b;
}//除法


//2.根运算和幂运算
//幂运算，任意数的任意次方（定义内）
double power(double base, double exponent)
{
	if (base == 0 && exponent == 0)
	{
		printf("错误！0的0次方无意义！\n");
		return 0;
	}
	if (base < 0 && exponent != (int)exponent)
	{
		//负数的非整数次方会产生复数结果
		printf("错误！负数的非整数次方会产生复数结果！此计算器不支持复数运算");
		return 0;
	}
	return pow(base, exponent);//调用math库的数学运算
}
//平方根运算
double squareRoot(double num)
{
	if (num < 0)
	{
		printf("错误!负数没有平方根！\n");
		return 0;
	}
	return sqrt(num);
}
//任意次方根运算
double nthRoot(double num, double n)
{
	if (n == 0)
	{
		printf("错误！开0次方无意义！\n");
		return 0;
	}
	if (num < 0 && fmod(n, 2) == 0)
	{
		printf("错误！负数的偶次方根无意义\n");
		return 0;
	}
	return pow(num, 1.0 / n);
}
// 平方（x²，本质是幂运算的特例）
// 注：平方功能在菜单中是选项8，实现时直接调用power(num1, 2)


//3.阶乘运算
double factorial(int n) 
{
	if (n < 0)
	{  // 阶乘仅定义于非负整数
		printf("错误：不能计算负数的阶乘！\n");
		return 0;
	}
	if (n == 0 || n == 1) 
	{
		return 1;  // 0! = 1，1! = 1
	}
	double result = 1;
	for (int i = 2; i <= n; i++) 
	{  // 循环计算2*3*...*n
	    result *= i;
	}
	return result;
}


//4.三角函数运算
//正弦运算
double sine(double angle, int isRadians)
{
	if (!isRadians)
	{
		// 如果是角度模式，先转换为弧度（角度 = 弧度 * 180/π，反之弧度 = 角度 * π/180）
		angle = angle * PI / 180.0;
	}
	return sin(angle);  // 调用math.h的sin函数（参数必须是弧度）
}
// 余弦函数（逻辑同正弦）
double cosine(double angle, int isRadians)
{
	if (!isRadians)
	{
		angle = angle * PI / 180.0;
	}
	return cos(angle);
}
// 正切函数（带无定义检查）
double tangent(double angle, int isRadians)
{
	if (!isRadians)
	{  
		// 角度转弧度
		angle = angle * PI / 180.0;
	}
	// 考虑正切无定义的情况
	if (fmod(angle + PI / 2, PI) == 0)
	{  
		// fmod是取模函数，判断是否为无定义点
		printf("错误：正切函数在90度+k×180度处无定义！\n");
		return 0;
	}
	return tan(angle);  // 调用math.h的tan函数
}

//5. 反三角函数（反正弦、反余弦、反正切）
// 反正弦（arcsin）
double arcsine(double value)
{
	if (value < -1 || value > 1)
	{  
		// arcsin的输入范围是[-1,1]
		printf("错误：反正弦函数的输入必须在[-1,1]范围内！\n");
		return 0;
	}
	double result = asin(value);  // 调用math.h的asin（返回弧度）
	// 根据模式返回弧度或角度（角度 = 弧度 × 180/π）
	return useRadians ? result : result * 180.0 / PI;//条件？表达式1（成立时输出）：表达式2（不成立时输出）
}
// 反余弦（arccos，逻辑同arcsin）
double arccosine(double value)
{
	if (value < -1 || value > 1)
	{
		printf("错误：反余弦函数的输入必须在[-1,1]范围内！\n");
		return 0;
	}
	double result = acos(value);
	return useRadians ? result : result * 180.0 / PI;
}
// 反正切（arctan，输入无范围限制）
double arctangent(double value)
{
	double result = atan(value);  // 调用math.h的atan（返回弧度）
	return useRadians ? result : result * 180.0 / PI;
}

//5.对数运算
// 任意底对数（log_base(num)）
double logarithm(double num, double base)
{
	if (num <= 0)
	{  
		// 真数必须>0
		printf("错误：对数的真数必须大于零！\n");
		return 0;
	}
	if (base <= 0 || base == 1)
	{  
		// 底数必须>0且≠1
		printf("错误：对数的底数必须大于0且不等于1！\n");
		return 0;
	}
	// 换底公式：log_b(a) = ln(a)/ln(b)（或lg(a)/lg(b)）
	return log(num) / log(base);
}

// 自然对数（ln，即底数为e的对数）
double naturalLog(double num) 
{
	if (num <= 0) 
	{  
		// 真数必须>0
		printf("错误：自然对数的真数必须大于零！\n");
		return 0;
	}
	return log(num);  // 调用math.h的log（默认是自然对数）
}
// 常用对数（log10，在菜单中是选项17，实现时调用logarithm(num1, 10)）



//7. 输入处理函数（解析数学常量和用户输入）
// 解析数学输入（支持数字、pi/π、e、带系数的pi如"2pi"）
double parseMathInput(char* input) {
	// 步骤1：清理输入中的空白字符（如空格、制表符），并转为小写（统一"PI"和"pi"）
	char cleaned[100];  // 存储清理后的字符串（声明了一个字符数组，名为cleaned）
	int j = 0;
	for (int i = 0; input[i] != '\0'; i++)
	{
		if (!isspace(input[i])) 
		{  
			// 跳过空白字符
			cleaned[j++] = tolower(input[i]);  // 转为小写
		}
	}
	cleaned[j] = '\0';  // 手动添加字符串结束符

	// 步骤2：检查是否是特殊常量（pi/π或e）
	if (strcmp(cleaned, "pi") == 0 || strcmp(cleaned, "π") == 0) 
	{
		return PI;  // 直接返回圆周率
	}
	else if (strcmp(cleaned, "e") == 0) {
		return E;   // 直接返回自然常数
	}

	// 步骤3：检查是否是带系数的pi（如"2pi"、"3.14*pi"、"5π"）
	else if (strstr(cleaned, "pi") != NULL || strstr(cleaned, "π") != NULL) 
	{
		// 找到"pi"或"π"在字符串中的位置
		char* pi_ptr = strstr(cleaned, "pi");
		if (!pi_ptr) pi_ptr = strstr(cleaned, "π");

		if (pi_ptr == cleaned)
		{  
			// 输入就是"pi"/"π"（无系数）
			return PI;
		}
		else
		{
			// 提取系数（如"2pi"中的"2"，"3.14π"中的"3.14"）
			char coefficient[50];  
			// 存储系数字符串
			// 从开头复制到"pi"/"π"之前的位置
			//用于临时存储提取的数字系数  
			// //"π" -> coefficient 为空（系数为1）
			strncpy(coefficient, cleaned, pi_ptr - cleaned);
			coefficient[pi_ptr - cleaned] = '\0';  // 手动结束

			// 如果系数为空（如"*pi"），默认系数为1
			if (strlen(coefficient) == 0) 
			{
				return PI;
			}

			// 将系数字符串转为数字（如"2"→2.0，"3.14"→3.14）
			double coeff = atof(coefficient);
			return coeff * PI;  // 系数×π
		}
	}

	// 步骤4：如果不是特殊常量，按普通数字解析（如"3.14"→3.14，"-2.5"→-2.5）
	return atof(input);  // atof将字符串转为double
}

// 获取用户输入的数字（调用parseMathInput处理）
double getNumberInput() 
{
	char input[100];  // 存储用户输入的字符串
	fgets(input, sizeof(input), stdin);  // 读取一行输入（包括空格、换行符）

	// 去除输入中的换行符（fgets会把回车\n也读入，需要去掉）
	input[strcspn(input, "\n")] = 0;  // strcspn找"\n"的位置，替换为结束符

	return parseMathInput(input);  // 解析处理后的输入
}

// 输入验证（简单判断输入是否有效）
int isValidInput() 
{
	if (feof(stdin))
	{  
		// 如果输入流结束（如用户按Ctrl+Z），返回无效
		return 0;
	}
	return 1;
}


//8. 交互显示函数（菜单和帮助信息）
// 显示操作菜单（列出所有可用功能）
void displayMenu() 
{
	printf("\n=== 科学计算器 ===\n");
	printf("1. 加法 (+)\n");
	printf("2. 减法 (-)\n");
	printf("3. 乘法 (*)\n");
	printf("4. 除法 (/)\n");
	printf("5. 幂运算 (x^y)\n");
	printf("6. 平方根 (√x)\n");
	printf("7. 任意次方根 (x^(1/n))\n");
	printf("8. 平方 (x²)\n");
	printf("9. 阶乘 (n!)\n");
	printf("10. 正弦 (sin)\n");
	printf("11. 余弦 (cos)\n");
	printf("12. 正切 (tan)\n");
	printf("13. 反正弦 (arcsin)\n");
	printf("14. 反余弦 (arccos)\n");
	printf("15. 反正切 (arctan)\n");
	printf("16. 自然对数 (ln)\n");
	printf("17. 常用对数 (log10)\n");
	printf("18. 任意底对数\n");
	printf("19. 切换角度/弧度模式 (当前: %s)\n", useRadians ? "弧度" : "角度");
	printf("20. 显示π和e\n");
	printf("0. 退出\n");
	printf("请选择操作: ");
}

// 显示支持的数学常量提示（引导用户正确输入）
void displayMathConstantsHelp() 
{
	printf("\n支持的数学常量输入:\n");
	printf("  - pi 或 π: 圆周率 (3.14159...)\n");
	printf("  - e: 自然常数 (2.71828...)\n");
	printf("  - 2pi, 3π 等: 带系数的圆周率\n");
	printf("  - 普通数字: 如 3.14, 45, -2.5 等\n\n");
}


//六、main 函数（程序入口，控制流程）
int main() {
	int choice;  // 存储用户选择的菜单编号
	double num1, num2, result;  // 存储输入的数字和计算结果
	int intNum;  // 用于阶乘（阶乘要求输入整数）

	// 程序启动提示
	printf("欢迎使用科学计算器！\n");
	displayMathConstantsHelp();  // 显示输入提示

	// 无限循环（直到用户选择0退出）
	while (1) 
	{
		displayMenu();  // 显示菜单

		// 步骤1：获取用户的菜单选择（整数）
		if (scanf("%d", &choice) != 1)
		{  // 如果输入不是整数（如字母）
			printf("输入无效，请输入数字！\n");
			// 清空输入缓冲区（避免错误输入残留，影响下次读取）
			while (getchar() != '\n');
			continue;  // 重新显示菜单
		}

		// 清空输入缓冲区（处理scanf留下的换行符）
		while (getchar() != '\n');

		// 步骤2：处理退出选择
		if (choice == 0) 
		{
			printf("感谢使用！再见！\n");
			break;  // 退出循环，程序结束
		}

		// 步骤3：根据用户选择，调用对应功能（switch-case分支）
		switch (choice)
		{
		case 1:  // 加法
			printf("输入第一个数: ");
			num1 = getNumberInput();  // 获取第一个数
			printf("输入第二个数: ");
			num2 = getNumberInput();  // 获取第二个数
			result = add(num1, num2);  // 计算
			printf("结果: %.6lf\n", result);  // 输出（保留6位小数）
			break;

		case 2: // 减法
			printf("输入第一个数: ");
			num1 = getNumberInput();
			printf("输入第二个数: ");
			num2 = getNumberInput();
			result = subtract(num1, num2);
			printf("结果: %.6lf\n", result);
			break;

		case 3: // 乘法
			printf("输入第一个数: ");
			num1 = getNumberInput();
			printf("输入第二个数: ");
			num2 = getNumberInput();
			result = multiply(num1, num2);
			printf("结果: %.6lf\n", result);
			break;

		case 4: // 除法
			printf("输入被除数: ");
			num1 = getNumberInput();
			printf("输入除数: ");
			num2 = getNumberInput();
			result = divide(num1, num2);
			if (num2 != 0) printf("结果: %.6lf\n", result);
			break;

		case 5: // 幂运算
			printf("输入底数: ");
			num1 = getNumberInput();
			printf("输入指数: ");
			num2 = getNumberInput();
			result = power(num1, num2);
			if (!(num1 == 0 && num2 == 0)) printf("结果: %.6lf\n", result);
			break;

		case 6: // 平方根
			printf("输入一个数: ");
			num1 = getNumberInput();
			result = squareRoot(num1);
			if (num1 >= 0) printf("结果: %.6lf\n", result);
			break;

		case 7: // 任意次方根
			printf("输入要开方的数: ");
			num1 = getNumberInput();
			printf("输入次方数: ");
			num2 = getNumberInput();
			result = nthRoot(num1, num2);
			if (num2 != 0 && !(num1 < 0 && fmod(num2, 2) == 0)) {
				printf("结果: %.6lf\n", result);
			}
			break;

		case 8: // 平方
			printf("输入一个数: ");
			num1 = getNumberInput();
			result = power(num1, 2);
			printf("结果: %.6lf\n", result);
			break;

		case 9: // 阶乘
			printf("输入一个非负整数: ");
			if (scanf("%d", &intNum) == 1) {
				while (getchar() != '\n'); // 清空缓冲区
				result = factorial(intNum);
				if (intNum >= 0) printf("结果: %.0lf\n", result);
			}
			else {
				printf("输入无效！\n");
				while (getchar() != '\n'); // 清空缓冲区
			}
			break;

		case 10: // 正弦
			printf("输入角度/弧度值 (支持pi, π, e等): ");
			num1 = getNumberInput();
			result = sine(num1, useRadians);
			printf("sin(%.6lf) = %.6lf\n", num1, result);
			break;

		case 11: // 余弦
			printf("输入角度/弧度值 (支持pi, π, e等): ");
			num1 = getNumberInput();
			result = cosine(num1, useRadians);
			printf("cos(%.6lf) = %.6lf\n", num1, result);
			break;

		case 12: // 正切
			printf("输入角度/弧度值 (支持pi, π, e等): ");
			num1 = getNumberInput();
			result = tangent(num1, useRadians);
			if (!(fmod(useRadians ? num1 + PI / 2 : num1 + 90, useRadians ? PI : 180) == 0)) {
				printf("tan(%.6lf) = %.6lf\n", num1, result);
			}
			break;

		case 13: // 反正弦
			printf("输入值 (-1 到 1): ");
			num1 = getNumberInput();
			result = arcsine(num1);
			if (num1 >= -1 && num1 <= 1) {
				printf("arcsin(%.6lf) = %.6lf %s\n", num1, result, useRadians ? "弧度" : "度");
			}
			break;

		case 14: // 反余弦
			printf("输入值 (-1 到 1): ");
			num1 = getNumberInput();
			result = arccosine(num1);
			if (num1 >= -1 && num1 <= 1) {
				printf("arccos(%.6lf) = %.6lf %s\n", num1, result, useRadians ? "弧度" : "度");
			}
			break;

		case 15: // 反正切
			printf("输入值: ");
			num1 = getNumberInput();
			result = arctangent(num1);
			printf("arctan(%.6lf) = %.6lf %s\n", num1, result, useRadians ? "弧度" : "度");
			break;

		case 16: // 自然对数
			printf("输入一个正数: ");
			num1 = getNumberInput();
			result = naturalLog(num1);
			if (num1 > 0) printf("ln(%.6lf) = %.6lf\n", num1, result);
			break;

		case 17: // 常用对数
			printf("输入一个正数: ");
			num1 = getNumberInput();
			result = logarithm(num1, 10);
			if (num1 > 0) printf("log10(%.6lf) = %.6lf\n", num1, result);
			break;

		case 18: // 任意底对数
			printf("输入真数: ");
			num1 = getNumberInput();
			printf("输入底数: ");
			num2 = getNumberInput();
			result = logarithm(num1, num2);
			if (num1 > 0 && num2 > 0 && num2 != 1) {
				printf("log_%.6lf(%.6lf) = %.6lf\n", num2, num1, result);
			}
			break;

		case 19:  // 切换角度/弧度模式
			useRadians = !useRadians;  // 取反（1→0，0→1）
			printf("已切换到%s模式\n", useRadians ? "弧度" : "角度");
			break;

		case 20:  // 显示π和e的值
			printf("π = %.15lf\n", PI);  // 高精度显示
			printf("e = %.15lf\n", E);
			break;

		default:  // 无效选择
			printf("无效的选择！请重新输入。\n");
			break;
		}
	}

	return 0;
}


















