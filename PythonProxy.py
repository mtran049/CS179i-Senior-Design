# -*- coding: cp1252 -*-
# <PythonProxy.py>
#
#Copyright (c) <2009> <Fábio Domingues - fnds3000 in gmail.com>
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
Copyright (c) <2009> <Fábio Domingues - fnds3000 in gmail.com> <MIT Licence>

				  **************************************
				 *** Python Proxy - A Fast HTTP proxy ***
				  **************************************

Neste momento este proxy é um Elie Proxy.

Suporta os métodos HTTP:
 - OPTIONS;
 - GET;
 - HEAD;
 - POST;
 - PUT;
 - DELETE;
 - TRACE;
 - CONENCT.

Suporta:
 - Conexões dos cliente em IPv4 ou IPv6;
 - Conexões ao alvo em IPv4 e IPv6;
 - Conexões todo o tipo de transmissão de dados TCP (CONNECT tunneling),
	 p.e. ligações SSL, como é o caso do HTTPS.

A fazer:
 - Verificar se o input vindo do cliente está correcto;
   - Enviar os devidos HTTP erros se não, ou simplesmente quebrar a ligação;
 - Criar um gestor de erros;
 - Criar ficheiro log de erros;
 - Colocar excepções nos sítios onde é previsível a ocorrência de erros,
	 p.e.sockets e ficheiros;
 - Rever tudo e melhorar a estrutura do programar e colocar nomes adequados nas
	 variáveis e métodos;
 - Comentar o programa decentemente;
 - Doc Strings.

Funcionalidades futuras:
 - Adiconar a funcionalidade de proxy anónimo e transparente;
 - Suportar FTP?.


(!) Atenção o que se segue só tem efeito em conexões não CONNECT, para estas o
 proxy é sempre Elite.

Qual a diferença entre um proxy Elite, Anónimo e Transparente?
 - Um proxy elite é totalmente anónimo, o servidor que o recebe não consegue ter
	 conhecimento da existência do proxy e não recebe o endereço IP do cliente;
 - Quando é usado um proxy anónimo o servidor sabe que o cliente está a usar um
	 proxy mas não sabe o endereço IP do cliente;
	 É enviado o cabeçalho HTTP "Proxy-agent".
 - Um proxy transparente fornece ao servidor o IP do cliente e um informação que
	 se está a usar um proxy.
	 São enviados os cabeçalhos HTTP "Proxy-agent" e "HTTP_X_FORWARDED_FOR".

"""

import socket, thread, select

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
		self.target.send('%s %s %s\n'%(self.method, path, self.protocol)+self.client_buffer)
		print("sending HEAD") #DEBUG
		self._read_write()
		self.method = temp_method

		#print ('%s %s %s\n'%(self.method, path, self.protocol)+'Range: bytes = 0 - %d\n'%(int(self.content_length),)+self.client_buffer)
		#DEBUGGING REQUESTS#
		print('%s %s %s\n'%(self.method, path, self.protocol) + self.range1 + self.client_buffer)
		print('%s %s %s\n'%(self.method, path, self.protocol) + self.range2 + self.client_buffer)

		self.target.send('%s %s %s\n'%(self.method, path, self.protocol) + self.range1 + self.client_buffer)
		self.target2.send('%s %s %s\n'%(self.method, path, self.protocol) + self.range2 + self.client_buffer)
		#TO DO: need to send another request to "target2" that GETs a different range of bytes

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
		self.target.connect(address)
		self.target2.connect(address)

	#"revolving door" to re-direct the packets in the right direction
	def _read_write(self):
		time_out_max = self.timeout/3
		socs = [self.client, self.target, self.target2]
		count = 0
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
							range_test = data.find('Content-Length')
							self.content_length = data[range_test + 16:data.find('Accept-Ranges')]
							self.content_length = self.content_length[:-2]

							self.range1 = 'Range: bytes=0-' + str(int(self.content_length)/2) + '\n'
							self.range2 = 'Range: bytes=' + str(int(self.content_length)/2 + 1) + '-\n'

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
									if self.merger1 == '':
										data = self.remove_header(data)
										self.merger1 = self.merger1 + data
								elif in_ == self.target2:
									if self.merger2 == '':
										data = self.remove_header(data)
										self.merger2 = self.merger2 + data
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
