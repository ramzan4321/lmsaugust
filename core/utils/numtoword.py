# This function convert 6 digit number to word number
def numtowords(n):
    list_one = ['zero','one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen','nineteen']
    dict = {'2':'twenty','3':'thirty','4':'fourty','5':'fifty','6':'sixty','7':'seventy','8':'eighty','9':'ninety'}
    num = str(int(n))
    x = len(num)
    if x == 5:
        word = ""
        if int(num[-5])>1:
            word += dict[num[-5]]+" "
            if int(num[-4]) > 0:
                word += list_one[int(num[-4])]+" thousand"
            else:
                word += " thousand"
        else:
            numm = int(''.join(e for e in str(num[0:2]) if e.isalnum()))
            word += list_one[numm]+" thousand"

        if int(num[-3]) > 0:
            word += " "+list_one[int(num[-3])] +" hundered"
        else:
            word += ""
        if int(num[-2]) > 1 :
            word += " "+dict[num[-2]]
        if int(num[-2]) == 1:
            numm = int(''.join(e for e in str(num[-2:]) if e.isalnum()))
            word += " "+list_one[numm]
        else:
            if int(num[-1]) != 0:
                word += " "+list_one[int(num[-1])]
                print(word)
            else:
                word += ""
        print(word)
    elif x == 4:
        word =""
        if int(num[-4]) > 0:
                word += " "+list_one[int(num[-4])]+" thousand "
        else:
            word += " thousand"
        if int(num[-3]) > 0:
            word += " "+list_one[int(num[-3])] +" hundered"
        else:
            word += ""
        if int(num[-2]) > 1 :
            word += " "+dict[num[-2]]
        if int(num[-2]) == 1:
            numm = int(''.join(e for e in str(num[-2:]) if e.isalnum()))
            word += " "+list_one[numm]
        else:
            if int(num[-1]) != 0:
                word += " "+list_one[int(num[-1])]
                print(word)
            else:
                word += ""
    elif x == 6:
        word =""
        word += " "+list_one[int(num[0])]+" lakh"
        if int(num[-5]) > 1:
            word += " "+dict[num[-5]]+" "
        if int(num[-4]) > 0:
                word += " "+list_one[int(num[-4])]+" thousand"
        else:
            word += " thousand"
        if int(num[-3]) > 0:
            word += " "+list_one[int(num[-3])] +" hundered"
        else:
            word += ""
        if int(num[-2]) > 1 :
            word += " "+dict[num[-2]]
        if int(num[-2]) == 1:
            numm = int(''.join(e for e in str(num[-2:]) if e.isalnum()))
            word += " "+list_one[numm]
        else:
            if int(num[-1]) != 0:
                word += " "+list_one[int(num[-1])]
                print(word)
            else:
                word += ""
    elif x == 3:
        word =""
        if int(num[-3]) > 0:
            word += " "+list_one[int(num[-3])] +" hundered"
        else:
            word += ""
        if int(num[-2]) > 1 :
            word += " "+dict[num[-2]]
        if int(num[-2]) == 1:
            numm = int(''.join(e for e in str(num[-2:]) if e.isalnum()))
            word += " "+list_one[numm]
        else:
            if int(num[-1]) != 0:
                word += " "+list_one[int(num[-1])]
                print(word)
            else:
                word += ""
    elif x == 4:
        word =""
        if int(num[-2]) > 1 :
            word += " "+dict[num[-2]]
        if int(num[-2]) == 1:
            numm = int(''.join(e for e in str(num[-2:]) if e.isalnum()))
            word += " "+list_one[numm]
        else:
            if int(num[-1]) != 0:
                word += " "+list_one[int(num[-1])]
            else:
                word += ""
    else:
        word = ""
        if int(num[-1]) != 0:
            word += " "+list_one[int(num[-1])]
        else:
            word += "Zero"
    return word

def fix_to_two_digit(num):
    _num = str(num).rstrip('0').rstrip('.')
    if len(_num) > 1:
        return _num
    else:
        return '0'+_num