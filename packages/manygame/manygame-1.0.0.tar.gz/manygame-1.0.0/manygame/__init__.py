#__init__.py
import random

def card():
    faces = ["three","four","five","six","seven","eight","nine","ten",
            "jack","queen","king","ace","two"]

    faceile = random.choice(faces)
    faceile2 = random.choice(faces)

    facefiles = faces.index(faceile)
    facefiles2 = faces.index(faceile2)

    print("[1][2][3][4][5][6][7][8][9][10][11][12][13]")

    playerA = int(input("你是玩家A,请输入你要抽取的牌："))
    while playerA > 13:
        playerA = int(input("没有这个牌，请重新输入："))

    input("请找到一名玩家来抽牌。如果找到，请按下回车继续游戏。。。")

    print("[1][2][3][4][5][6][7][8][9][10][11][12][13]")

    playerB = int(input("你是玩家B,请输入你要抽取的牌："))
    while playerB > 13:
        playerB = int(input("没有这个牌，请重新输入："))

    input("计算中，请按下回车继续游戏。。。")

    if facefiles > facefiles2:
        print("A玩家的牌是",faceile,"B玩家的牌是",faceile2)
        print("A玩家赢了！")
    elif facefiles < facefiles2:
        print("A玩家的牌是",faceile,"B玩家的牌是",faceile2)
        print("B玩家赢了！")
    else:
        print("A玩家的牌是",faceile,"B玩家的牌是",faceile2)
        print("平局！")

    input("按下回车结束游戏。。。")

def numbergame():
    inputnum = int(input("请输入你想要最大的随机数："))
    number = random.randint(1,inputnum)

    guess = int(input("请输入你猜的数："))
    jh = 10
    print("你有",jh,"次机会来猜测。")

    while guess != number:
        if guess < number:
            print(guess,"数太小了")
        else:
            print(guess,"数太大了")
        jh -= 1
        if jh == 0:
            print("机会用完了，答案是",number)
            break
        else:
            print("你有",jh,"次机会来猜测。")
        guess = int(input("猜错了！请重新输入你猜的数："))
    if guess != number:
        print()
    else:
        print("恭喜你猜对了！答案是",number)
    input("按下回车键退出。。。")

def generate_maze(size=5):
    maze = [[" " for _ in range(size)] for _ in range(size)]
    # 放置玩家 (P) 和出口 (E)
    maze[0][0] = "P"
    maze[size-1][size-1] = "E"
    # 随机放置障碍物 (X)
    for _ in range(size):
        x, y = random.randint(0, size-1), random.randint(0, size-1)
        if maze[x][y] == " ":
            maze[x][y] = "X"
    return maze

def playmg():
    print("=== 迷宫探险 ===")
    print("用 WASD 移动，P=玩家，E=出口，X=障碍物")
    maze = generate_maze()
    px, py = 0, 0

    while True:
        for row in maze:
            print(" ".join(row))
        move = input("输入方向 (W/A/S/D): ").upper()

        new_px, new_py = px, py
        if move == "W" and px > 0:
            new_px -= 1
        elif move == "S" and px < len(maze)-1:
            new_px += 1
        elif move == "A" and py > 0:
            new_py -= 1
        elif move == "D" and py < len(maze)-1:
            new_py += 1
        else:
            print("无效移动！")
            continue

        if maze[new_px][new_py] == "X":
            print("撞到障碍物了！")
            continue
        elif maze[new_px][new_py] == "E":
            print("恭喜逃出迷宫！")
            break

        maze[px][py] = " "
        maze[new_px][new_py] = "P"
        px, py = new_px, new_py

if __name__ == "__main__":
    playmg()

def playsjb():
    print("=== 石头剪刀布 ===")
    choices = ["石头", "剪刀", "布"]
    while True:
        user_choice = input("输入你的选择（石头/剪刀/布，或输入 q 退出）: ").strip()
        if user_choice == "q":
            break
        if user_choice not in choices:
            print("无效输入！请重试。")
            continue
        
        computer_choice = random.choice(choices)
        print(f"电脑出了: {computer_choice}")

        # 判断胜负
        if user_choice == computer_choice:
            print("平局！")
        elif (user_choice == "石头" and computer_choice == "剪刀") or \
             (user_choice == "剪刀" and computer_choice == "布") or \
             (user_choice == "布" and computer_choice == "石头"):
            print("你赢了！")
        else:
            print("你输了！")

if __name__ == "__main__":
    playsjb()

