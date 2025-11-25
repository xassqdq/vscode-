import time
import random
import pygame
import math
import sys
from datetime import datetime

# =========================================爱心窗口基础设置===========================================
# Initialize Pygame（保持初始化，但不提前创建窗口）
pygame.init()

# Constants
xScreen = 1200
yScreen = 800
PI = 3.1415926535
e = 2.71828
average_distance = 0.162
quantity = 506
circles = 210
frames = 20

# Colors
colors = [
    (255, 138, 180), (255, 144, 194), (255, 144, 194),
    (255, 143, 195), (255, 142, 190), (255, 142, 193),
    (255, 145, 196)
]


# 移除全局的窗口创建代码，移到root1()函数内

class Point:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color


def screen_x(x):
    return x + xScreen / 2


def screen_y(y):
    return -y + yScreen / 2


def create_random(x1, x2):
    if x2 > x1:
        return random.randint(x1, x2)
    return x1  # Fallback to x1 if x2 <= x1


def create_data():
    origin_points = []
    points = []

    # Generate original points on the heart curve
    for radian in range(10, int(2 * PI * 1000), 5):  # Convert radians to degrees and scale
        radian /= 1000.0
        x2 = 16 * math.pow(math.sin(radian), 3)
        y2 = 13 * math.cos(radian) - 5 * math.cos(2 * radian) - 2 * math.cos(3 * radian) - math.cos(4 * radian)
        if len(origin_points) == 0 or math.sqrt(
                math.pow(x2 - origin_points[-1].x, 2) + math.pow(y2 - origin_points[-1].y, 2)) > average_distance:
            origin_points.append(Point(x2, y2, None))

    # Generate points with varying sizes and colors
    lightness = 1.5
    for size in range(10, 200, 1):  # Scale size from 0.1 to 20
        size /= 10.0
        success_p = 1 / (1 + math.pow(e, 8 - size / 2))
        if lightness > 1:
            lightness -= 0.0025
        for point in origin_points:
            if success_p > random.random():
                color_index = create_random(0, 6)
                r, g, b = colors[color_index]
                adjusted_color = (
                    max(0, min(255, int(r / lightness))),
                    max(0, min(255, int(g / lightness))),
                    max(0, min(255, int(b / lightness)))
                )
                points.append(
                    Point(size * point.x + create_random(-4, 4), size * point.y + create_random(4, 4), adjusted_color))

    images = []
    for frame in range(frames):
        image = pygame.Surface((xScreen, yScreen), pygame.SRCALPHA)
        image.fill((0, 0, 0, 0))  # Fill with transparent background

        # Draw points with increasing distance
        for point in points:
            distance = math.sqrt(point.x ** 2 + point.y ** 2)
            distance_increase = -0.0009 * distance * distance + 0.35714 * distance + 5
            x_increase = distance_increase * point.x / distance / frames
            y_increase = distance_increase * point.y / distance / frames
            point.x += x_increase
            point.y += y_increase
            pygame.draw.circle(image, point.color, (int(screen_x(point.x)), int(screen_y(point.y))), 1)

        # Draw additional points with randomness
        for size in range(170, 230, 3):  # Scale size from 17 to 23
            size /= 10.0
            for point in origin_points:
                if (random.random() > 0.6 and size >= 20) or (size < 20 and random.random() > 0.95):
                    if size >= 20:
                        x_offset = create_random(-(frame * frame // 5 - 15), frame * frame // 5 + 15)
                        y_offset = create_random(-(frame * frame // 5 - 15), frame * frame // 5 + 15)
                    else:
                        x_offset = create_random(-5, 5)
                        y_offset = create_random(-5, 5)
                    x = point.x * size + x_offset
                    y = point.y * size + y_offset
                    color_index = create_random(0, 6)
                    pygame.draw.circle(image, colors[color_index], (int(screen_x(x)), int(screen_y(y))), 1)

        images.append(image)

    return images


def root1():
    # 在这里创建窗口，仅当调用root1()时才会执行
    screen = pygame.display.set_mode((xScreen, yScreen))
    pygame.display.set_caption("Heart Animation")

    clock = pygame.time.Clock()
    images = create_data()
    extend = True
    shrink = False
    frame = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0, 0, 0))
        screen.blit(images[frame], (0, 0))
        pygame.display.flip()
        clock.tick(50)  # Adjust the frame rate

        if extend:
            frame = 19 if frame == 19 else frame + 1
        else:
            frame = 0 if frame == 0 else frame - 1

        if frame == 19:
            extend = False
            shrink = True
        elif frame == 0:
            shrink = False
            extend = True

    pygame.quit()
    # 注释掉sys.exit()，避免关闭窗口后退出整个程序
    # sys.exit()


def love_calculator(name1, name2):
    """可爱的缘分计算器"""
    # 处理name1 == name2的异常情况
    if name1 == name2:
        print(f"\n⚠️  异常提示：不能和自己计算缘分哦！{name1} 要找个小伙伴呀～")
        return

    print(f"\n正在计算 {name1} 💕 {name2} 的缘分...")
    time.sleep(2)

    # 假装在计算
    for i in range(5):
        print("🔮" * (i + 1))
        time.sleep(0.3)

    # 核心计算逻辑不变
    score = (len(name1) + len(name2)) * 5 + random.randint(1, 20)
    score = min(score, 100)
    if name1 == "朱诗怡" and name2 == "叶志鸿":
        score =100
        print(f"\n✨ 缘分指数: {score}% ✨")
    elif name2 == "朱诗怡" and name1 == "叶志鸿":
        score =100
        print(f"\n✨ 缘分指数: {score}% ✨")
    print(f"\n✨ 缘分指数: {score}% ✨")

    # 优先判断name2是否为叶志鸿
    if name1 == "朱诗怡" and name2 == "叶志鸿":
        print("天作之合！你们是命中注定的一对朋友！💘")
    elif name1 == "朱诗怡" and name2 == "叶志鸿":
        print("天作之合！你们是命中注定的一对朋友！💘")
    elif score >= 90:
        print("天作之合！你们是命中注定的一对朋友！💘")
    elif score >= 70:
        print("超级般配！继续加油哦！💕")
    elif score >= 50:
        print("很有潜力！多多了解对方吧！💝")
    else:
        print("需要更多努力来培养感情呢！🌱")


def print_compliments():
    """随机播放赞美"""
    compliments = [
        "你今天看起来真漂亮！✨",
        "你的笑容让世界变得更美好！🌞",
        "你是个非常特别的人！🌟",
        "和你在一起总是很开心！😊",
        "你的内在美和外在美一样闪耀！💎",
        "你让周围的人都感到快乐！🎉",
        "你是个充满智慧和魅力的人！🔮",
        "你的存在让这个世界更美好！🌍",
        "你有着令人惊叹的个性！🎨",
        "你是我见过最棒的人之一！🏆"
    ]

    print("\n🎁 特别为你准备的赞美：")
    for i in range(3):
        compliment = random.choice(compliments)
        print(f"💌 {compliment}")
        time.sleep(1)


def funny_fortune():
    """有趣的运势预测"""
    fortunes = [
        "今天会有好事发生！准备迎接惊喜吧！🎊",
        "今天适合尝试新事物，勇敢迈出第一步！🚀",
        "你的魅力值今天爆表！好好利用这个机会！💫",
        "今天会遇到让你开心的小确幸！🍀",
        "保持微笑，好运自然来！😄",
        "今天是你闪耀的日子！✨",
        "美好的事物正在向你走来！🌈",
        "今天会有意想不到的收获！🎁"
    ]

    print(f"\n🔮 今日运势：{random.choice(fortunes)}")


def countdown_surprise():
    """倒计时惊喜"""
    print("\n倒计时惊喜即将开始！")
    for i in range(5, 0, -1):
        print(f"🎯 {i}...")
        time.sleep(1)

    surprises = [
        "你值得世界上所有的美好！",
        "今天要对自己好一点哦！",
        "记住，你比自己想象的更优秀！",
        "生活因你而精彩！",
        "继续保持你的独特魅力！"
    ]

    print(f"\n🎊 惊喜：{random.choice(surprises)}")


def main():
    print("=" * 50)
    print("🌟 专属快乐程序 🌟")
    print("=" * 50)

    name = input("请输入你的名字：")

    print(f"\n欢迎 {name}！这个程序是特别为你准备的！🎀")
    time.sleep(1)

    while True:
        print("\n请选择你想要的功能：")
        print("1. 💖 跳动的心形")
        print("2. 🔮 缘分计算器")
        print("3. 🌟 随机赞美")
        print("4. 🍀 今日运势")
        print("5. 🎊 倒计时惊喜")
        print("6. 🎉 全部来一遍")
        print("7. ❤️ 退出程序")

        choice = input("\n请输入选择 (1-7): ")

        if choice == '1':
            root1()
        elif choice == '2':
            name2 = input("请输入另一个人的名字：")
            love_calculator(name, name2)
        elif choice == '3':
            print_compliments()
        elif choice == '4':
            funny_fortune()
        elif choice == '5':
            countdown_surprise()
        elif choice == '6':
            root1()
            print_compliments()
            funny_fortune()
            countdown_surprise()
        elif choice == '7':
            print(f"\n再见 {name}！希望你今天过得开心！💝")
            break
        else:
            print("请输入有效的选择哦！")

        time.sleep(1)


if __name__ == "__main__":
    main()