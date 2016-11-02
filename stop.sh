for i in $(ps ax|grep "\-\-name NapNapDEV -w 3"|grep -Po "([0-9]{5,6})");do
	kill $i;
done
