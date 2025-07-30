import cmath as pak
def complexsqrtcalc ():
    while True:
        ask = int(input("enter a number to show complex root of "))
        print(pak.sqrt(ask))
        stop=input("would you like to continue ")
        while stop!="yes":
            return " "

print(complexsqrtcalc())

