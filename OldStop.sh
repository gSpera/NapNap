for i in $(pgrep gunicorn);do 
	kill $i;
done
