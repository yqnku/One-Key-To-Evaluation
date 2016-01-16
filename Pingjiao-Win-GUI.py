import httplib
import re
import os
import binascii
import wx

def Encrypt(pwd):
    publicKey = int("00b6b7f8531b19980c66ae08e3061c6295a1dfd9406b32b202a59737818d75dea03de45d44271a1473af8062e8a4df927f031668ba0b1ec80127ff323a24cd0100bef4d524fdabef56271b93146d64589c9a988b67bc1d7a62faa6c378362cfd0a875361ddc7253aa0c0085dd5b17029e179d64294842862e6b0981ca1bde29979",16)
    pwd = pwd[::-1]
    pwdAscii = binascii.b2a_hex(pwd)
    pwdAscii = int(pwdAscii,16)
    password = pwdAscii**65537%publicKey
    password = hex(password)[2:-1]
    if len(password) != 256:
        add = '0'* (256-len(password))
        password = add + password
    return password

class MyFrame(wx.Frame):
    def __init__(self, calc = False):
        wx.Frame.__init__(self, parent = None, title = "一键评教", size = (280, 380))
        self.panel = wx.Panel(self, -1)       
        label_id=wx.StaticText(self.panel,1008,"学号")
        label_id.SetPosition(wx.Point(15, 15))
        label_psw=wx.StaticText(self.panel,1009,"密码")
        label_psw.SetPosition(wx.Point(15, 65))
        label_val=wx.StaticText(self.panel,1010,"验证码")
        label_val.SetPosition(wx.Point(15, 165))
        
        self.text_id=wx.TextCtrl(self.panel,1005)
        self.text_id.SetPosition(wx.Point(120, 15))
        self.text_psw=wx.TextCtrl(self.panel,1006,style=wx.TE_PASSWORD)
        self.text_psw.SetPosition(wx.Point(120, 65))
        self.text_val=wx.TextCtrl(self.panel,1007)
        self.text_val.SetPosition(wx.Point(120, 165))
        
        button = wx.Button(self.panel, 1003, "退出")
        button.SetPosition(wx.Point(120, 215))
        wx.EVT_BUTTON(self, 1003, self.OnCloseMe)
        wx.EVT_CLOSE(self, self.OnCloseWindow)

        self.button = wx.Button(self.panel, 1004, "评教")
        self.button.SetPosition(wx.Point(30, 215))
        wx.EVT_BUTTON(self, 1004, self.OnPressMe)

        #get cookie
        conn=httplib.HTTPConnection("222.30.32.10")
        conn.request("GET","/")
        res=conn.getresponse()
        self.cookie=res.getheader("Set-Cookie")
        conn.close()
        self.headers= {"Content-Type":"application/x-www-form-urlencoded","Cookie":self.cookie}
        #get ValidateCode
        conn=httplib.HTTPConnection("222.30.32.10")
        conn.request("GET","/ValidateCode","",self.headers)
        res=conn.getresponse()
        f=open("ValidateCode.jpg","w+b")
        f.write(res.read())
        f.close()
        conn.close()

        image=wx.Image("ValidateCode.jpg",wx.BITMAP_TYPE_JPEG)
        val=wx.StaticBitmap(self.panel,bitmap=image.ConvertToBitmap())
        val.SetPosition(wx.Point(15, 115))

    def OnCloseMe(self, event):
        self.Close(True)

    def OnPressMe(self, event):
        #显示请稍候
        self.button.SetLabel("请稍候")
        
        stu_id=self.text_id.GetValue()
        psw=self.text_psw.GetValue()
        val=self.text_val.GetValue()
        params="operation=&usercode_text="+stu_id+"&userpwd_text="+Encrypt(psw)+"&checkcode_text="+val+"&submittype=%C8%B7+%C8%CF"
        conn=httplib.HTTPConnection("222.30.32.10")
        conn.request("POST","/stdloginAction.do",params,self.headers);
        res=conn.getresponse()
        loginInfo = res.read().decode('gb2312')
        if loginInfo.find(unicode("用户不存在或密码错误","gb2312")) != -1:
            info = "用户不存在或密码错误\n请重新打开软件后重试"
        elif loginInfo.find(unicode("请输入正确的验证码","gb2312")) != -1:
            info = "验证码输入错误\n请重新打开软件后重试"
        elif loginInfo.find('stdtop') == -1:
            info = "未知错误"
        else:
            info = "登录成功"

        self.label_status=wx.StaticText(self.panel,1009,info)
        self.label_status.SetPosition(wx.Point(50, 248))
        if info != "登录成功":
            return
        
        conn.close()
        conn=httplib.HTTPConnection("222.30.32.10")
        conn.request("GET","/evaluate/stdevatea/queryCourseAction.do","",self.headers);
        res=conn.getresponse()
        content=res.read()
        num=int(re.findall(r"共 ([0-9]*) 项",content)[0])
        conn.close()
        failcount=0
        for i in range(num):
            conn=httplib.HTTPConnection("222.30.32.10")
            conn.request("GET","/evaluate/stdevatea/queryTargetAction.do?operation=target&index="+str(i),"",self.headers);
            res=conn.getresponse()
            content=res.read()
            content=content.replace("该教师给你的总体印象","该教师给你的总体印象（10）")
            #中文括号
            item=re.findall(r"（([0-9]*)）",content)
            conn.close()
            #submit
            conn=httplib.HTTPConnection("222.30.32.10")
            params="operation=Store"
            
            for j in range(len(item)):  params+=("&array["+str(j)+"]="+item[j])
            params+="&opinion="
            self.headers= {"Content-Type":"application/x-www-form-urlencoded"
                  ,"Cookie":self.cookie,"Referer":"http://222.30.32.10/evaluate/stdevatea/queryTargetAction.do?operation=target&index="+str(i)}
            conn.request("POST","/evaluate/stdevatea/queryTargetAction.do",params,self.headers);
            rescontent=conn.getresponse().read()
            if -1==rescontent.find("成功保存！"):failcount+=1
            conn.close()
        #提示成功
        s="完成!\n总共: %d\n成功: %d" % (num,num-failcount)
        self.label_status=wx.StaticText(self.panel,1008,s)
        self.label_status.SetPosition(wx.Point(50, 265))    
        os.remove("ValidateCode.jpg")
        
    def OnCloseWindow(self, event):
        self.Destroy()
if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame()
    frame.Show(True)
    app.MainLoop()
