var http = require('http');
var io = require('socket.io')(http);

http.listen(9504,function(){
	console.log('listening on port 9504');
});

io.on('connection' ,function(socket){
	socket.on('joined',function(data){
		console.log(data);
		socket.emit('ack','recieved');
	});
});
