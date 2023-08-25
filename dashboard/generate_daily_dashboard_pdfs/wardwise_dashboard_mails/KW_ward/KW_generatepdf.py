from datetime import datetime
import ast
import os
import time

file_data = open("/home/mcgm/Development/mcgm/mcgm/dashboard/loaddatafast/KW_warddata.txt", "r", encoding="utf-8")    #CHANGE
contents = file_data.read()
resultdict = ast.literal_eval(contents)
file_data.close()


htmltemplate = open("/home/mcgm/Development/mcgm/mcgm/static/html2pdf/final-html/index.html", "r", encoding="utf-8")
htmltemplatecontents = htmltemplate.read()

count = 0
sendflag = 0
for each_online in reversed(resultdict['data']['online']):
    count+=1
    htmltemplatecontents = htmltemplatecontents.replace("tablebodyrows", "<tr><td>"+str(count)+"</td><td>"+str(each_online['veh'])+"</td><td>"+str(each_online['type'])+"</td><td>"+str(each_online['ward'])+"</td><td>"+str(each_online['time'])+"</td><td>"+str(each_online['veh_ward'])+"</td><td>"+str(each_online['veh_contractor'])+"</td></tr>"+"\ntablebodyrows")

onlinevehicle_count = count
htmltemplatecontents = htmltemplatecontents.replace("totalonlinevehicles", str(onlinevehicle_count))
if(count < 1):
    sendflag = 0
else:
    sendflag = 1


for each_offline in reversed(resultdict['data']['offline']):
    count+=1
    htmltemplatecontents = htmltemplatecontents.replace("tablebodyrows", "<tr><td>"+str(count)+"</td><td>"+str(each_offline['veh'])+"</td><td>"+str(each_offline['type'])+"</td><td>"+str(each_offline['ward'])+"</td><td>"+str(each_offline['time'])+"</td><td>"+str(each_offline['veh_ward'])+"</td><td>"+str(each_offline['veh_contractor'])+"</td></tr>"+"\ntablebodyrows")


offlinevehicle_count = count - onlinevehicle_count
htmltemplatecontents = htmltemplatecontents.replace("totalofflinevehicles", str(offlinevehicle_count))

htmltemplatecontents = htmltemplatecontents.replace("totalnumberofvehicles", str(count))
htmltemplatecontents = htmltemplatecontents.replace("tablebodyrows", "")

now = datetime.now()
#dd/mm/YY H:M:S
dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
htmltemplatecontents = htmltemplatecontents.replace("currentdatetime", dt_string)



htmltemplate2 = open("/home/mcgm/Development/mcgm/mcgm/static/html2pdf/final-html/index2.html", "w", encoding="utf-8")
htmltemplate2.write(htmltemplatecontents)
htmltemplate2.close()

cmd = '/usr/local/bin/wkhtmltopdf --enable-local-file-access /home/mcgm/Development/mcgm/mcgm/static/html2pdf/final-html/index2.html /home/mcgm/Development/mcgm/mcgm/static/html2pdf/final-html/index2.pdf'
os.system(cmd)
time.sleep(2)

cmd2 = 'scp /home/mcgm/Development/mcgm/mcgm/static/html2pdf/final-html/index2.pdf root@205.147.109.56:/home/ajit_cleanupmumbai_minorwork/wardwise_dashboard_mails/KW_ward/dashboard.pdf'
os.system(cmd2)



f = open("/home/mcgm/Development/mcgm/mcgm/dashboard/generate_daily_dashboard_pdfs/wardwise_dashboard_mails/KW_ward/sendadminreportflag.txt", "w")
f.write(str(sendflag))
f.close()



cmd3 = 'scp /home/mcgm/Development/mcgm/mcgm/dashboard/generate_daily_dashboard_pdfs/wardwise_dashboard_mails/KW_ward/sendadminreportflag.txt root@205.147.109.56:/home/ajit_cleanupmumbai_minorwork/wardwise_dashboard_mails/KW_ward/sendadminreportflag.txt'
os.system(cmd3)
time.sleep(1)