# -*- coding: cp1252 -*-
# <PythonProxy.py>
#
#Copyright (c) <2009> <F�bio Domingues - fnds3000 in gmail.com>
#
#Permission is hereby granted, free of charge, to any person
#obtaining a copy of this software and associated documentation
#files (the "Software"), to deal in the Software without
#restriction, including without limitation the rights to use,
#copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the
#Software is furnished to do so, subject to the following
#conditions:
#
#The above copyright notice and this permission notice shall be
#included in all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#OTHER DEALINGS IN THE SOFTWARE.

"""\
Copyright (c) <2009> <F�bio Domingues - fnds3000 in gmail.com> <MIT Licence>

				  **************************************
				 *** Python Proxy - A Fast HTTP proxy ***
				  **************************************

Neste momento este proxy � um Elie Proxy.

Suporta os m�todos HTTP:
 - OPTIONS;
 - GET;
 - HEAD;
 - POST;
 - PUT;
 - DELETE;
 - TRACE;
 - CONENCT.

Suporta:
 - Conex�es dos cliente em IPv4 ou IPv6;
 - Conex�es ao alvo em IPv4 e IPv6;
 - Conex�es todo o tipo de transmiss�o de dados TCP (CONNECT tunneling),
	 p.e. liga��es SSL, como � o caso do HTTPS.

A fazer:
 - Verificar se o input vindo do cliente est� correcto;
   - Enviar os devidos HTTP erros se n�o, ou simplesmente quebrar a liga��o;
 - Criar um gestor de erros;
 - Criar ficheiro log de erros;
 - Colocar excep��es nos s�tios onde � previs�vel a ocorr�ncia de erros,
	 p.e.sockets e ficheiros;
 - Rever tudo e melhorar a estrutura do programar e colocar nomes adequados nas
	 vari�veis e m�todos;
 - Comentar o programa decentemente;
 - Doc Strings.

Funcionalidades futuras:
 - Adiconar a funcionalidade de proxy an�nimo e transparente;
 - Suportar FTP?.


(!) Aten��o o que se segue s� tem efeito em conex�es n�o CONNECT, para estas o
 proxy � sempre Elite.

Qual a diferen�a entre um proxy Elite, An�nimo e Transparente?
 - Um proxy elite � totalmente an�nimo, o servidor que o recebe n�o consegue ter
	 conhecimento da exist�ncia do proxy e n�o recebe o endere�o IP do cliente;
 - Quando � usado um proxy an�nimo o servidor sabe que o cliente est� a usar um
	 proxy mas n�o sabe o endere�o IP do cliente;
	 � enviado o cabe�alho HTTP "Proxy-agent".
 - Um proxy transparente fornece ao servidor o IP do cliente e um informa��o que
	 se est� a usar um proxy.
	 S�o enviados os cabe�alhos HTTP "Proxy-agent" e "HTTP_X_FORWARDED_FOR".

"""

import socket, thread, select, re

__version__ = '0.1.0 Draft 1'
BUFLEN = 8192
VERSION = 'Python Proxy/'+__version__
HTTPVER = 'HTTP/1.1'

class ConnectionHandler:
	def __init__(self, connection, address, timeout):
		self.client = connection
		self.client_buffer = ''
		self.timeout = timeout
		#merger1 and merger2 used to merge data in read_write function
		self.merger1 = ''
		self.merger2 = ''
		self.content_length = 0
		self.range1 = ''
		self.range2 = ''
	
			
		#print the request and it extracts the protocol and path
		self.method, self.path, self.protocol = self.get_base_header()
	
	
		if self.method=='CONNECT':
			self.method_CONNECT()
	
		#handle the GET request
		elif self.method in ('OPTIONS', 'GET', 'HEAD', 'POST', 'PUT',
							 'DELETE', 'TRACE'):
			self.method_others()
	
		self.client.close()
		self.target.close()
		self.target2.close()
	
	def get_base_header(self):
		while 1:
			self.client_buffer += self.client.recv(BUFLEN)
			end = self.client_buffer.find('\n')
			if end!=-1:
				break

		#print the request
		print '%s'%self.client_buffer[:end]#debug

		data = (self.client_buffer[:end+1]).split()
		self.client_buffer = self.client_buffer[end+1:]
		return data

	def method_CONNECT(self):
		self._connect_target(self.path)
		self.client.send(HTTPVER+' 200 Connection established\n'+
						 'Proxy-agent: %s\n\n'%VERSION)
		self.client_buffer = ''
		self._read_write()        

	#forward the packet to its final destination
	def method_others(self):
		self.path = self.path[7:]
		i = self.path.find('/')
		host = self.path[:i]        
		path = self.path[i:]
		self._connect_target(host)

		#TO DO: first find out the Content-Length by sending a RANGE request

		#testing RANGE request
		temp_method = self.method
		self.method = 'HEAD'
		self.target.send('%s %s %s\r\n'%(self.method, path, self.protocol)+self.client_buffer)
		print("sending HEAD") #DEBUG
		self._read_write()
		self.method = temp_method

		#prepare message1 and message2 for server in correct format
		message1 = self.method + ' ' + path + ' ' + self.protocol + '\r\n'
		message2 = self.method + ' ' + path + ' ' + self.protocol + '\r\n'
		split_buff = self.client_buffer.split('\r\n')
		for x in split_buff: #find Host first and removes from list
			if x.find('Host') != -1:
				message1 = message1 + x + '\r\n'
				message2 = message2 + x + '\r\n'
				split_buff.remove(x)
		message1 = message1 + self.range1
		message2 = message2 + self.range2
		for x in split_buff:
			if x != '':
				message1 = message1 + x + '\r\n'
				message2 = message2 + x + '\r\n'
		message1 = message1 + '\r\n'
		message2 = message2 + '\r\n'
		
		#DEBUGGING REQESTS#
		print message1.split(' ')
		print message2

		self.target.send(message1)
		self.target2.send(message2)

		self.client_buffer = ''

		#start the read/write function
		print 'Start second read write'
		self._read_write()

	def _connect_target(self, host):
		i = host.find(':')
		if i!=-1:
			port = int(host[i+1:])
			host = host[:i]
		else:
			port = 80
		(soc_family, _, _, _, address) = socket.getaddrinfo(host, port)[0]
		self.target = socket.socket(soc_family)
		self.target2 = socket.socket(soc_family)
		#TODO BIND SOCKETS TO INTERFACES
		self.target.bind((wireless ip address, port number))
		self.target2.bind((ethernet address, port number))
		self.target.connect(address)
		self.target2.connect(address)

	#"revolving door" to re-direct the packets in the right direction
	def _read_write(self):
		time_out_max = self.timeout/3
		socs = [self.client, self.target, self.target2]
		count = 0
		header1_flag = True
		header2_flag = True
		while 1:
			(recv, _, error) = select.select(socs, [], socs, 3)
			if error:
				print 'ERROR: broke out of read_write'
				break
			if recv:
				for in_ in recv:
					data = in_.recv(BUFLEN)
					if in_ is self.client:
						out = self.target
					else:
						out = self.client
					if data:
						#Check if it's response to the RANGE request and extract the Content-Length
						print self.method
						if self.method == 'HEAD':
							split_data = re.split(' |\r\n', data)
							content_index = split_data.index('Content-Length:')
							self.content_length = split_data[content_index + 1]

							self.range1 = 'Range: bytes=0-' + str(int(self.content_length)/2) + '\r\n'
							self.range2 = 'Range: bytes=' + str(int(self.content_length)/2 + 1) + '-' + self.content_length + '\r\n'

							print 'range 1: ' + self.range1
							print 'range 2: ' + self.range2

							print (data)
							out.send(data)
							return
						#If it is not a RANGE request, merge the recieved data from both interfaces
						else:
							print 'Not a RANGE request'
							if out == self.client:
								if in_ == self.target:
									if (self.merger1.find('\r\n\r\n') != -1) and header1_flag:
										self.merger1 = self.remove_header(self.merger1)
										header1_flag = False
									self.merger1 = self.merger1 + data
								elif in_ == self.target2:
									if (self.merger2.find('\r\n\r\n') != -1) and header2_flag:
										self.merger2 = self.remove_header(self.merger2)
										header2_flag = False
									self.merger2 = self.merger2 + data
								print 'Bytes Recieved:'
								print len(self.merger1) + len(self.merger2)
								print 'Bytes Needed:'
								print self.content_length
								if str(len(self.merger1) + len(self.merger2)) == str(self.content_length):
									print '(DEBUG) Data merged'
									data = self.merger1 + self.merger2 + 'HTTP/1.1 200 OK\r\n\r\n'
									print data[:200]
									out.send(data)
									self.merger1 = ''
									self.merger2 = ''
									break
							else:
								out.send(data)
								break

	def remove_header(self, input_data):
		index = input_data.find('\r\n\r\n')
		print input_data[:index]
		return input_data[index + 4:]

#start the proxy server and listen for connections on port 8080
def start_server(host='localhost', port=8080, IPv6=False, timeout=60,
				  handler=ConnectionHandler):
	if IPv6==True:
		soc_type=socket.AF_INET6
	else:
		soc_type=socket.AF_INET
	soc = socket.socket(soc_type)
	soc.bind((host, port))
	print "Serving on %s:%d."%(host, port)#debug
	soc.listen(0)
	while 1:
		thread.start_new_thread(handler, soc.accept()+(timeout,))

if __name__ == '__main__':
	start_server()
