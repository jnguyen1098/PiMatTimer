import tkinter as tk
import threading
from gpiozero import Button
from time import time
import random
import sys
import os
import logging
import _thread
from subprocess import call
from pyTwistyScrambler.pyTwistyScrambler import scrambler333

class Stopwatch:
    
    def __init__(self):

        self.root = tk.Tk()
        self.root.title('CubeTimer')
        self.root.attributes('-fullscreen', True)
        self.root.config(cursor="none") 

        self.lastScramble = ""
        logging.basicConfig(filename="/home/pi/CubeTimer/solves.txt",format='%(message)s',filemode='a')
        self.logger=logging.getLogger()  
        self.logger.setLevel(logging.DEBUG)  

        #timer label
        self.display = tk.Label(self.root, text='0.00', font = ("Arial Bold", 50))
        self.display.place(relx = 0.5, rely = 0.48, anchor = 'center')

        #listbox and scrollbar
        self.scrollbar = tk.Scrollbar(self.root)
        self.solvesList = tk.Listbox(self.root, height = 14, width = 58, yscrollcommand = self.scrollbar.set,font = ("Arial 11 bold")) 
        self.scrollbar.config(command = self.solvesList.yview)       

        #ao5 label
        self.ao5Label = tk.Label(self.root, text='ao5: ', font = ("Arial 13 bold"))
        self.ao5Label.place(relx = 0.5, rely = 0.64, anchor = 'center')

        #ao12 label
        self.ao12Label = tk.Label(self.root, text='ao12: ', font = ("Arial 13 bold")) 
        self.ao12Label.place(relx = 0.5, rely = 0.72, anchor = 'center')
        
        #view solves button
        self.infoButton = tk.Button(self.root,text = 'View Solves',width= 40,font = ("Arial 12 bold"),command=self.view_solves)
        self.infoButton.place(relx = 0.5, rely = 0.92, anchor = 'center') 

        #back button
        self.backButton = tk.Button(self.root,text = 'Back',font = ("Arial 12 bold"),command=self.view_timer)  
        
        #delete selected button
        self.removeSelected = tk.Button(self.root,text = 'Delete',font = ("Arial 12 bold"),command=self.remove_selected)  
        
        #exit button
        self.exit = tk.Button(self.root,text = 'Exit',font = ("Arial 12 bold"),command=self.exit)  

        #shutdown button
        self.shutdown = tk.Button(self.root,text = 'Shutdown',font = ("Arial 12 bold"),command=self.shutdown)  

        #get first scramble from file then delete it from the file then generate new scramble in a new thread
        stream = os.popen('head -n 1 /home/pi/CubeTimer/scrambles.txt')
        scramblestr = stream.read() 
        os.system('tail -n +2 "/home/pi/CubeTimer/scrambles.txt" > "/home/pi/CubeTimer/tmp.txt" && mv "/home/pi/CubeTimer/tmp.txt" "/home/pi/CubeTimer/scrambles.txt"')       
        _thread.start_new_thread(self.scramble3,())
              
        #fill up listbox and get average
        if os.path.isfile("/home/pi/CubeTimer/solves.txt"):
            solveFile = open("/home/pi/CubeTimer/solves.txt")
            solveArray = []
    
            x = 1

            for line in solveFile:
                if x < 10:
                    solveArray.append("  " + str(x) + ") " + str(line).strip())
                else:
                    solveArray.append(str(x) + ") " + str(line).strip())
                x += 1
    
            solveArray.reverse()
    
            for i in range(len(solveArray)):
                current = solveArray[i].split(" - ")
                self.solvesList.insert(tk.END,current[0])
                self.solvesList.insert(tk.END,current[1])
                self.solvesList.insert(tk.END," ") 

            solveFile.close()

            self.set_average(5) 
            self.set_average(12)            
    
        #scramble label
        #split scramble in half and put second half on new line to increase readability 
        middle = int(len(scramblestr)/2)

        if scramblestr[middle] == " ":
            scramblestr = scramblestr[:middle] +  "\n" + scramblestr[middle:]
        elif scramblestr[middle + 1] == " ":
            scramblestr = scramblestr[:middle + 1] +  "\n" + scramblestr[middle + 1:]
        else:
            scramblestr = scramblestr[:middle - 1] +  "\n" + scramblestr[middle -1 :]

        self.scramble = tk.Label(self.root, text= scramblestr, font = ("Arial 14 bold")) 
        self.scramble.place(relx = 0.5, rely = 0.13, anchor = 'center')

        #GPIO pins 19 and 26
        self.button1 = Button(19)
        self.button2 = Button(26)
 
        self.paused = True

        self.checkInput()  
        self.root.mainloop()
        

    #toggle the timer on and off
    def toggle(self):
        
        if self.paused:
            self.paused = False
            self.oldtime = time()
            self.run_timer()
        else:
            self.paused = True
            self.oldtime = time()

    #timer that updates the label
    def run_timer(self):
        
        if self.paused:
            return
        
        delta = (time() - self.oldtime)
        secstr = '%.2f' % delta
        minstr = int(delta /60)
        hourstr = int(minstr/60)
        
        if(minstr > 0):
            secstr = '%.2f' % (delta - (minstr * 60))
            if delta - (minstr * 60) < 10:
                self.display.config(text= str(minstr) + ":0" + secstr)
            else:
                self.display.config(text= str(minstr) + ":" + secstr)
        else:
            self.display.config(text=secstr)
        
        self.display.after(10, self.run_timer)

    def checkInput(self):

        if self.button1.is_pressed and self.button2.is_pressed:

            if not self.paused:                

                self.display.config(foreground = "red")
   
                lastTime = self.display.cget("text")
                self.toggle()

                #this appends to a log file lawl
                solveStr = lastTime + " - " + self.lastScramble.replace("\n", "") 
                self.logger.info(solveStr) 
                print(solveStr)

                self.solvesList.insert(0, ") " + lastTime) 
                self.solvesList.insert(1,self.lastScramble.replace("\n", ""))
                self.solvesList.insert(2," ")

                #print(self.solvesList.size())

                self.set_average(5)                                  
                self.set_average(12)

                self.display.update_idletasks()

                self.ao5Label.place(relx = 0.5, rely = 0.64, anchor = 'center')
                self.ao12Label.place(relx = 0.5, rely = 0.72, anchor = 'center')
                self.scramble.place(relx = 0.5, rely = 0.13, anchor = 'center')
                self.infoButton.place(relx = 0.5, rely = 0.92, anchor = 'center') 

                os.system('tail -n +2 "/home/pi/CubeTimer/scrambles.txt" > "/home/pi/CubeTimer/tmp.txt" && mv "/home/pi/CubeTimer/tmp.txt" "/home/pi/CubeTimer/scrambles.txt"')       
                _thread.start_new_thread(self.scramble3, ())
                #os.system('cd /home/pi/pyTwistyScrambler; python3 3x3.py;')
       

                self.button1.wait_for_release()
                self.button2.wait_for_release()

                self.display.config(foreground = "black")

            else:
                self.display.config(foreground = "green")
                self.infoButton.place_forget() 
                self.scramble.place_forget()
                self.ao5Label.place_forget()
                self.ao12Label.place_forget()

                self.lastScramble = self.scramble.cget("text")
                self.display.update_idletasks() 

                self.button1.wait_for_release()
                self.button2.wait_for_release()

                stream = os.popen('head -n 1 /home/pi/CubeTimer/scrambles.txt')
                scramblestr = stream.read()
              
                #split scramble in half and put second half on new line to increase readability 
                middle = int(len(scramblestr)/2)

                if scramblestr[middle] == " ":
                    scramblestr = scramblestr[:middle] +  "\n" + scramblestr[middle:]
                elif scramblestr[middle + 1] == " ":
                    scramblestr = scramblestr[:middle + 1] +  "\n" + scramblestr[middle + 1:]
                else:
                    scramblestr = scramblestr[:middle - 1] +  "\n" + scramblestr[middle -1 :]
 
                self.scramble.config(text = scramblestr)

                self.display.config(foreground = "black")
                self.toggle()

        self.display.after(10,self.checkInput)

    def view_solves(self):

        self.solvesList.pack(side = tk.LEFT,anchor = tk.NW,fill = tk.X)
        self.scrollbar.pack(side = tk.RIGHT, fill = tk.BOTH)
        self.backButton.place(relx = 0.11, rely = 0.92, anchor = 'center')
        self.ao5Label.place(relx = 0.5, rely = 0.65, anchor = 'center')
        self.removeSelected.place(relx = 0.35, rely = 0.92, anchor = 'center') 
        self.exit.place(relx = 0.57, rely = 0.92, anchor = 'center') 
        self.shutdown.place(relx = 0.83, rely = 0.92, anchor = 'center')

        self.solvesList.delete(0,tk.END)

        if os.path.isfile("/home/pi/CubeTimer/solves.txt"):
            solveFile = open("/home/pi/CubeTimer/solves.txt")
            solveArray = []
    
            x = 1

            for line in solveFile:
                if x < 10:
                    solveArray.append("  " + str(x) + ") " + str(line).strip())
                else:
                    solveArray.append(str(x) + ") " + str(line).strip())
                x += 1
    
            solveArray.reverse()
    
            for i in range(len(solveArray)):
                current = solveArray[i].split(" - ")
                self.solvesList.insert(tk.END,current[0])
                self.solvesList.insert(tk.END,current[1])
                self.solvesList.insert(tk.END," ") 

            solveFile.close() 
        
        self.ao5Label.place_forget()
        self.ao12Label.place_forget()
        self.scramble.place_forget()
        self.infoButton.place_forget() 
        self.display.place_forget()

    def remove_selected(self):
        
        selection = self.solvesList.curselection()
        selectedArray = self.solvesList.get(selection[0]).split(") ") 

        if not (len(selectedArray) > 1):
            return

        if ":" in selectedArray[1]:
            selectedArray[1].replace(':','')
            
        #if isinstance(float(selectedArray[1].rstrip()),float):
        self.solvesList.delete(selection[0],selection[0]+2)
            
        lineToDelete = selectedArray[0].strip()
        deleteString = "sed -i '{0}d' /home/pi/CubeTimer/solves.txt".format(lineToDelete)
        os.system(deleteString)
        print("Deleted solve #" + lineToDelete + ": " +selectedArray[1])

        self.set_average(5)
        self.set_average(12)
        self.view_solves()
        self.solvesList.see(selection[0])

    def view_timer(self):
        self.scramble.place(relx = 0.5, rely = 0.13, anchor = 'center')
        self.infoButton.place(relx = 0.5, rely = 0.92, anchor = 'center') 
        self.display.place(relx = 0.5, rely = 0.48, anchor = 'center')
        self.ao5Label.place(relx = 0.5, rely = 0.64, anchor = 'center')
        self.ao12Label.place(relx = 0.5, rely = 0.72, anchor = 'center')

        self.backButton.place_forget()
        self.solvesList.pack_forget()
        self.scrollbar.pack_forget()
        self.removeSelected.place_forget()
        self.exit.place_forget()
        self.shutdown.place_forget()

    def set_average(self, number):
        
        if self.solvesList.size() >= ((number*3) - 1):

            aoArray = []

            for i in range(0,number*3,3):
                if ":" in self.solvesList.get(i).split(") ")[1]:
                    minute = self.solvesList.get(i).split(") ")[1].split(":")
                    secondsToAdd = float(float(minute[0]) * 60)
                    aoArray.append(float(float(minute[1]) + secondsToAdd))
                else:
                    aoArray.append(float(self.solvesList.get(i).split(") ")[1])) 
                                               
            #for k in range(number):
                #print(aoArray[k])                
 
            top = aoArray[0]
            bot = aoArray[0]
            total = 0

            #print(len(aoArray))
                    
            for j in range(number):
                if aoArray[j] > top:
                    top = aoArray[j]
                if aoArray[j] < bot:
                    bot = aoArray[j]
                    
            for j in range(number):
                if not aoArray[j] == top and not aoArray[j] == bot:
                    total += aoArray[j]
                    
            average = '%.2f' % (total / (number - 2))
            if number == 5:
                self.ao5Label.config(text= "ao5: " + str(average)) 
            if number == 12:
                self.ao12Label.config(text= "ao12: " + str(average)) 
        else:
            if number == 5:
                self.ao5Label.config(text= "ao5: ") 
            if number == 12:
                self.ao12Label.config(text= "ao12: ") 

    def scramble3(self):
        with open("/home/pi/CubeTimer/scrambles.txt","a") as scrambleFile:
            print("Generating new 3x3 scramble")
            scrambleFile.write(scrambler333.get_WCA_scramble() + os.linesep)
            print("Generation complete")
                                                                                     
    def exit(self):
        quit()

    def shutdown(self):
        call("sudo nohup shutdown -h now", shell=True)
 
Stopwatch()
