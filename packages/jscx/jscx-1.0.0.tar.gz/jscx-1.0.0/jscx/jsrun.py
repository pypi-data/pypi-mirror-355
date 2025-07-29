import tkinter

class JzXt:
    def __init__(self, root):
        self.root = root
        self.root.title("结账系统")
        self.root.geometry("1500x1000")
        self.xt()
        self.xt2()
        
    def xt(self):
        tslabel = tkinter.Label(self.root,text="提示：负数符号当它不存在\n    就行")
        tslabel.place(x=1, y=1)

        label1 = tkinter.Label(self.root,text="请输入商品价格：")
        label1.place(x=50, y=60)

        self.entry = tkinter.Entry(self.root)
        self.entry.place(x=50, y=90)

        label2 = tkinter.Label(self.root,text="请输入商品个数：")
        label2.place(x=50, y=120)

        self.entry2 = tkinter.Entry(self.root)
        self.entry2.place(x=50, y=150)

        self.label3 = tkinter.Label(self.root,text="共计：0")
        self.label3.place(x=50, y=180)

        label4 = tkinter.Label(self.root,text="应给：")
        label4.place(x=50, y=210)

        self.entry3 = tkinter.Entry(self.root)
        self.entry3.place(x=100, y=210)

        self.label5 = tkinter.Label(self.root,text="还钱/给钱：")
        self.label5.place(x=50, y=240)

        self.label6 = tkinter.Label(self.root,text="信息：")
        self.label6.place(x=50, y=270)

        button1 = tkinter.Button(self.root,text="结账",command=self.jiez)
        button1.place(x=50, y=300)

    def jiez(self):
        gj = float(self.entry.get()) * float(self.entry2.get())
        self.label3.config(text=f"共计：{gj}")
        y2 = eval(self.entry3.get())
        yg2 = gj - y2
        self.label5.config(text=f"还钱/给钱：{yg2}")
        if yg2 < 0:
            self.label6.config(text="信息：还钱")
        elif yg2 > 0:
            self.label6.config(text="信息：不够钱")
        elif yg2 == 0:
            self.label6.config(text="信息：够钱")

    def xt2(self):
        ts2label = tkinter.Label(self.root,text="多个物品结账")
        ts2label.place(x=1000, y=1)

        label5 = tkinter.Label(self.root,text="请输入左边计算出商品的多个价格：如：50+30")
        label5.place(x=1000, y=60)

        self.entry4 = tkinter.Entry(self.root)
        self.entry4.place(x=1000, y=90)

        self.label7 = tkinter.Label(self.root,text="共计：0")
        self.label7.place(x=1000, y=180)

        label8 = tkinter.Label(self.root,text="应给：")
        label8.place(x=1000, y=210)

        self.entry6 = tkinter.Entry(self.root)
        self.entry6.place(x=1050, y=210)

        self.label8 = tkinter.Label(self.root,text="还钱/给钱：")
        self.label8.place(x=1000, y=240)

        self.label9 = tkinter.Label(self.root,text="信息：")
        self.label9.place(x=1000, y=270)

        button2 = tkinter.Button(self.root,text="结账",command=self.jiezduo)
        button2.place(x=1000, y=300)

    def jiezduo(self):
        gj2 = eval(self.entry4.get())
        self.label7.config(text=f"共计：{gj2}")
        y1 = eval(self.entry6.get())
        yg = gj2 - y1
        self.label8.config(text=f"还钱/给钱：{float(yg)}")
        if yg < 0:
            self.label9.config(text="信息：还钱")
        elif yg > 0:
            self.label9.config(text="信息：不够钱")
        elif yg == 0:
            self.label9.config(text="信息：够钱")

def run():
    root = tkinter.Tk()
    app = JzXt(root)
    root.mainloop()

if __name__ == "__main__":
    run()