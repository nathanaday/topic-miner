# EE450: Introduction to Computer Networks - Midterm Exam

**University of Southern California**  
**October 2, 2020**

**Part 1: True/False** 25%  
**Part 2: Quickies** 38%  
**Part 3: Error Detection** 10%  
**Part 4: Error/Flow Control** 15%  
**Part 4: DNS, HTTP & Web Caching** 12%  
**Total** 100%

**Notes:**
- You can work the problems in any order you wish (the goal is to try to accumulate as many points as you can). If you get stuck in one problem, go to another.
- All your answers must be on the exam paper.

**Rules:**
- This is a closed book, closed notes exam. You are only allowed one post card 5"×7" of formulas ONLY and a Calculator.
- Adherence to the University's Code of Ethics will be strictly monitored and enforced. Academic Integrity violations, such as cheating, will result in a series of actions and penalties including the student failing the class.

# Part 1: True or False

## 1. True or False

### a.
The BW × Delay product is the maximum # of bits/sec that can fill the "pipe"

### b.
In stop and wait ARQ, the receiver always sends an ACK frame each time it receives a frame with the wrong sequence number

### c.
In sliding window flow control, there can never be more outstanding frames than the receive window size.

### d.
It impossible for two TCP sockets on a client host A, both bound to the same local IP address and local port number, to communicate with two different servers B and C respectively.

### e.
A root name server can return an authoritative response for any domain name.

### f.
The number of name servers that must be contacted to resolve www.usc.edu from a client located outside of usc.edu. (Presume no entries are cached anywhere) is 3

### g.
ARP is a protocol used to resolve the "next hop IP address" to its MAC address.

### h.
A process C running in a server has a port number of 30. Two hosts A and B each send a UDP datagram to host C with destination port number 30. Both datagrams will be directed to the same socket.

### i.
In Statistical TDM, the number of time slots in each frame is less than the number of input lines to the MUX.

### j.
If a computer has multiple Network Interface Cards, The DHCP process must occur separately over each interface to obtain a separate dynamically assigned IP address for each interface.

### k.
A socket is a protocol that defines the messages exchanged between Peer applications layers (i.e. the client and the server applications)

### l.
An Ethernet adapter (NIC) passes every non-corrupt frame that it receives up to the network layer.

### m.
HTML protocol transfers files that make up pages on the world wide web

### n.
Recursive DNS queries require shorter socket connections with DNS servers than Iterative DNS requests

### o.
A DHCP server must be located on every network to assign IP addresses to DHCP clients on that network

### p.
It takes a single bit ten times longer to propagate over a 10Mb/s link than over a 100 Mbps link

### q.
The end-to-end delay in transferring a message over a store and forward network is in general lower if the message is broken into packets due to parallelism.

### r.
UDP does not have the same concept of persistent connection as TCP

### s.
Bit stuffing ensures that all frames are the same size and that the flag pattern does not appear in the payload of the frame

### t.
TCP is a transport layer protocol that provides guarantees on Reliability, Delay and Throughput

### u.
There are 3 entities (Two clients and a mail server) involved when Alice sends an e-mail to Bob.

### v.
Suppose Client A initiates a Telnet session with Server S. At about the same time, Client B also initiates a Telnet session with Server S. If A and B are different hosts, is it permissible that the source port number in the segments from A to S is the same as that from B to S.

## Multiple Choice Questions

### w.
By using Web caching,
a. We can reduce delay for all objects even those that are was cached
b. We can reduce traffic on an institution's access link
c. The cache acts as both client and server
d. All the above responses are correct
e. b and c only

### x.
When a TCP segment belonging to an existing connection arrives at a host, in order to direct the datagram to the appropriate socket, the operating system's network stack uses the following fields:
a. The source IP address.
b. The destination IP address
c. The source port number
d. The destination port number

### y.
When a UDP Datagram arrives at a host, the operating system's network stack uses the following fields to direct the datagram to the appropriate socket
a. The source IP address.
b. The destination IP address
c. The source port number
d. The destination port number

# Part 2: Quickies (every blank is worth 2 point)

## 1.
Consider a transmission link that uses the stop and wait protocol. The ratio of the propagation delay to the transmission time is 3. Frames are transmitted at a rate of 10 Mbps and each frame is 1k bits long. Bits propagate $2 \times 10^8$ m/sec.
- The length of the link is ______________ meter.
- The link utilization is __________ %

## 2.
Five sources are multiplexed using FDM on a link that has a total bandwidth of 4000 Hz. The maximum bandwidth for each source if there must be a 200 Hz guard band between the channels is _____________ Hz

## 3.
Suppose the following bits arrive at the DLC layer at receiver.
0111111001011111011011110101001111110
The payload is __________________________________

## 4.
Consider a situation in which 1000 clients are trying to download a 10 MB file from a server. If the server has a 100 Mb/s access link and the clients have access links with a downstream rate of 2 Mb/s each, how long does it take to download the file to all clients; under ideal conditions (you may ignore the time to establish a TCP connection to the server). Answer: ___________________ sec. Now, consider the peer-to-peer situation, in which there is no server and one peer holds the file to be distributed. Assuming that the upstream rate from each peer is 1 Mb/s and the downstream rate is 2 Mb/s, how long does it take to distribute the file to all peers? Answer: _______________ sec.

## 5.
We have 4 information sources, generating traffic at rates 2Kbps, 3Kbps, 4Kbps and 5Kbps respectively. They are to be multiplexed using synchronous TDM with each time slot carrying 2 bits. Each source is active 50% of the time. Ignore any synchronization bits.
a. The minimum number of time slots per frame is = _________ slots
b. The multiplexer rate is ________________ bps
c. The TDM frame rate is ______________ frames/sec

## 6.
We have 4 information sources, generating traffic, when active, at rates 10Kbps, 15Kbps, 20Kbps and 30Kbps respectively. The sources are active 25%, 50%, 75% and 100% respectively. A Statistical TDM with a link utilization of 75% is used. The required data rate at the output of the MUX is __________ bps.

## 7.
Two packets are transmitted back-to-back over a two hops network. The length of each packet is 1000 bits. The data rate on the first hop is 1Mbps. Each hop is 500 meters long and the propagation speed is $2.5 \times 10^8$ m/sec. The second packet experience queuing delay at the router of 3 msec. The data rate of the second hop is _____________ bps. The end-to-end delay to deliver both packets is _____________ sec. The throughput is __________ bps (assume there are no errors)

## 8.
A user in Los Angeles, connected to the internet via a 20 Mb/s (b=bits) connection retrieves a 250 KB (B=Bytes) web page from a server in Seattle, where the page references 4 images of 1 MB each. Assume that the one way propagation delay is 25 ms.

a. Approximately how long does it take for the page (including images) to appear on the user's screen, assuming non-persistent HTTP using a single connection at a time? Answer: ___________________ sec

b. Repeat part "a" assuming persistent HTTP. Answer: ___________________ sec

c. Repeat part "a" assuming persistent HTTP with pipelining. Answer: ___________________ sec

d. Repeat part "a" assuming non-persistent HTTP with 3 parallel connections. Answer: ___________________ sec

## 9.
Three clients B, C, D are communicating with a server node A. with the indicated Source and Destination Port numbers. From this diagram determine, what is the "total" number of sockets does "A" have to open assuming
- UDP Sockets: ____________
- TCP Sockets: _____________

[Figure: Network diagram showing server A connected to clients B, C, D with various source ports (SP) and destination ports (DP) labeled]

# Part 3: Error Detection

## 3.
An FCS error detection mechanism is used over a communications link. The message bit sequence is 101011. An FCS generator pattern of 1011 is used to generate the FCS sequence.

### a)
How many FCS bits are generated? What are they? What is the transmitted bit sequence? Identify the FCS bits in that sequence. Show details of your work.

### b)
Now suppose the received sequence is 010010111. Was it received correctly? If so, what was the message sequence according to the receiver? If not, can you tell how many bit errors occurred? Show your work

### c)
Now suppose the channel introduces the following error sequence 100010111. Will the receiver be able to detect the error? Prove your answer analytically.

# Part 4: Sliding Window ARQ

Consider a link that uses Go-Back-N ARQ protocol with SWS=4. Suppose the transmission time of a frame is 1 second. A time-out mechanism (for the oldest unacknowledged frame in the window) of 2 seconds (The time-out timer starts when you transmit the first bit of your frame) is set. Assume that one-way propagation delay is 0.5 seconds. Neglect the processing delay. Upon receiving a frame, the receiver will wait 1 second and send an accumulative ACK for all frames received with no errors up to that point in time (If none is received with no errors, the receiver will repeat the last ACK he sent). Neglect the transmission time of the ACK frame. Assume that station A begins with frame $F_0$. Draw the frame-exchange-timing diagram for the following sequence of events. Acknowledgements are sequenced as follows: $ACK_n$ means receiver is acknowledging all frames up to and including frame n. Frames are 1000 bits long.

- Assume that station A has ONLY 5 frames to send, starting at t=0. Frame $F_2$ was received and detected to be in error and $F_4$ was lost in transmission. Calculate the throughput and the link utilization

# Part 5: Name Resolution and Web Browsing

Client A wants to download a webpage http://example.net/index.html from the web server H. The web page is 1G-bit long. Client A does NOT know the IP address of Server H. Client A already got his IP address and the IP address of the local DNS (Server C) from the DHCP server (Server B). Assume:
- DNS commands and http commands are so small compared to the file such that you can ignore their transmission times (ONLY)
- The propagation delay within the LAN is negligible. The propagation delay between servers E, F, H and I to the Router is 100 msec.
- The LAN operates at 1 Gbps. Each Link between servers E, F, H and I to the Router operate at 100 Mbps.
- The DNS is iterative
- DNS runs over UDP where as HTTP runs over TCP.

[Figure: Network topology diagram showing Client A, DHCP Server B, DNS Server C, Switch D, Router G, and servers E, F, H, I connected through the network infrastructure]

## Answer the following questions:

### a.
How many total Networks are there in the diagram (2 points)

### b.
Calculate the time elapsed from the moment user A enters the URL till the time the file is completely downloaded. Create a table that identifies the steps taken (in order) along with the time required to accomplish each step (do NOT accumulate time in each step), After you are done with the steps you MUST add to find out the total time (You may add more rows if needed)

| Step | Action | Delay (msec) |
|------|--------|--------------|
| 1    |        |              |
| 2    |        |              |
| 3    |        |              |
| 4    |        |              |
| 5    |        |              |
| 6    |        |              |
| 7    |        |              |
| 8    |        |              |
| 9    |        |              |
| 10   |        |              |
| 11   |        |              |
| 12   |        |              |
| 13   |        |              |