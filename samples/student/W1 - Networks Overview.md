
### Course Overview

Part 1: Data Communications & Networking
Part 2: Computer Networking Protocols (TCP/IP)
Part 3: Wide Area Networks (WANs)
Part 4: Local Area Networks (LANS)
Part 5: Interne overemyhvices (Routers, Switches, etc.)
Part 6: Transport Layer Protocols
Part 7: Network Applications
Part 8: Network Security

>[!tip] Lecture 1
>- Much of this lecture gets into some physical differences between a telephone network and the internet 
>	- physical links
>	- private vs. public networks
>	- e.g. a preview into how packets flow through a network topology


### Computer Networks

**A Computer(?) Network** is a set of nodes such as routers, switches, hosts, etc. interconnected via transmission facilities for the purpose of providing services to end systems/users
- ﻿﻿So why the question mark?? Non-traditional end systems (Laptops, Cell Phones, Tablets, gaming Consoles, Sensor devices, Toasters, Refrigerators, etc...) are being connected to the internet
- ﻿﻿Point-to-point communication is not practical!  
    Devices are too far apart  
    Large set of devices would need impractical number of connections. See illustration next chart

### Generic Computer Network

![[Screenshot 2026-01-13 at 11.58.13 AM.png]]

**Dedicated transmission facilities** are those that are used by you only (the first link between the host and the internet), e.g. fiber line, coper line

**Shared transmission facilities** may be shared between multiple end nodes, carries traffic from many, many users
- Higher capacity

### Example: Telephone Network

![[Screenshot 2026-01-13 at 11.55.07 AM.png]]
**Fully connected topology** - every node is connected to every other node via a dedicated link
- However, this is wasteful or impossible (rare to see this in the real world, only if you string together a few home PCs)
- assumes few number of devices in the same physical vicinity; cannot extend dedicated links to new nodes very far away

![[Screenshot 2026-01-13 at 11.57.28 AM.png]]
Now replace the fully connected topology with a centralized network switch
- Nodes are not directly connected, but all **links are still dedicated**

### Clients, Servers and Peers  
- A network computer can either provide service or request service  
- A **server** is a service provider, providing access to network resources  
- A **Client** is a service requester  
- A **Peer-to-Peer** network does not have a dedicated server. All computers are equal, and they both provide and request services

### Server Roles

Servers can assume several roles and a single server could also have several roles  

Examples of Servers include:  
- File Servers: Manages user access to shared files  
- Print Servers: Manages user access to print resources  
- Application Servers: Similar to FS with some processing  
- Mail Servers: Manages electronic messages between users  
- Communications (Remote Access) Servers: Manages data flow and e-messages from one network to another  
- Web Servers: Runs WWW and FTP servers for access via the Internet/Intranet  
- Directory (DNS) Servers: Locates information about networks such as domains.

### Network Applications

- E-mail
- WWW
- Instant messaging
- Remote login
- P2P file sharing
- Multi-user network games
- Streaming audio/video (YouTube, Hulu, Netflix)
- Search
- Voice over IP (e.g. Skype)
- Real-time video conferencing
- High definition and 4K video
- On-line Social Network (Facebook, Twitter, etc.)
- E-Commerce
- Distributed Databases

### Link Duplicity

- Simplex - one direction (e.g. Radio, broadcasting)
- Half Duplex (HDX) - either direction but only one way at a time (e.g. police radio, walkie talkie)
- Full Duplex (FDX) - Both directions at the same time (e.g. telephone)


### Client Server Architecture

**Server:**
- ﻿﻿Always-on host
- ﻿﻿Permanent IP address
- ﻿﻿Data centers for scaling

**Clients:**
- ﻿﻿Communicate with server
- ﻿﻿May be intermittently connected
- ﻿﻿May have dynamic IP addresses
- ﻿﻿Do not communicate directly with each other



### P2P Architecture

- ﻿﻿No always-on server
- ﻿﻿arbitrary end systems directly communicate
- ﻿﻿Peers request service from other peers, provide service in return to other peers
	- ﻿﻿self scalability - new peers bring new service capacity, as well as new service demands
- ﻿﻿Peers are intermittently connected and change IP addresses (e.g. Bit Torrent)
	- ﻿﻿complex management (No central Control)

### Connection-Less Packet Switching

>[!warning] Attention
>There is NO guarantee that packets will be received in order or even received at all
> - Each packet may not follow the same route: routers make a decision on a router by router basis
> - Why are they received out of order? one reason: each packet has to "wait in line" (buffer)

Resource contention:
- aggregate resource demand can exceed amount available
- congestion: packets queue, wait for link use
- store and forward: packets move one hop at a time Node receives complete packet before forwarding

queuing and loss:
- ﻿﻿if arrival rate (in bps) to link exceeds transmission rate of link for a period of time:
	- ﻿﻿packets will queue, wait to be transmitted on link
	- ﻿﻿packets can be dropped (lost) if memory (buffer) fills up

### Cloud Service Providers

**Network cloud vs. Computing cloud**
- **Network cloud** is your ISP (spectrum, Verizon, etc.) - they don't deal with content, they only deal with connectivity
- **Computing cloud** - provide processing, computing, and data storage capabilities

### Network Software

- NOS include special functions for connecting hosts into a network
- ﻿﻿NOS manages network resources and services
- ﻿﻿NOS provide network security for multiple users
- ﻿﻿Most common Client/Server NOS include:
	- ﻿﻿UNIX/LINUX
	- ﻿﻿Microsoft Windows
	- ﻿﻿Novell Netware
	- ﻿﻿0S/2
	- ﻿﻿Others
- Network hosts communicate through the use of client software called "Shells, Redirectors, Requesters"
- ﻿﻿Network Protocols (such as **TCP/IP**, SPX/IPX, NETBEUI, etc..) enables data transmission across the network
- ﻿﻿Client software resides on top of the network protocols.
---

## Network Classifications

- Networks could be classified as switched or shared (broadcasted)
- Networks could also be classified based on their functionalities for example Backbone Networks, Content Delivery Networks, Overlay Networks

## Local Area Network (II)

![[Screenshot 2026-01-20 at 11.07.30 AM.png]]

A "hub" is a dumb device, it does not understanding the meaning of any of the traffic. It only understands "0s and 1s"
- IP address 32 bits
- MAC address 48 bits

In the diagram above, when any client computer sends an "envelope" with a destination mac address, the hub sends the envelope to all machines on the LAN. The machine's drop the envelopes themselves if the destination MAC does not match their own MAC

The router is responsible for making sure internal LAN traffic does not reach the ISP


## (Aside) Packet Flow

**How packets travel:**

**Within your LAN (192.168.0.10 → 192.168.0.20):**

- Device uses ARP to find MAC address
- Packet goes directly from source to destination
- MAC addresses used, router not involved

**To the Internet (192.168.0.10 → 8.8.8.8):**

1. Your device sends packet to router's MAC address (found via ARP)
2. Router receives it, performs NAT (replaces your private IP with its public IP)
3. Router forwards to next hop, using _that_ router's MAC address (found via ARP on the router's external network)
4. At each router hop across the Internet, MAC addresses change but IP addresses stay the same (except for the NAT translation at your edge)

**Key point:** MAC addresses are only used for **local delivery** on each network segment. They get replaced at every router hop. NAT is a separate function that translates IP addresses at the network boundary.

## Home Networks

![[Screenshot 2026-01-20 at 11.37.51 AM.png]]

Typical home networks
- Cable modem
- Router/firewall/NAT
- Ethernet
- Wireless access point

A router may have multiple interfaces. Each of them is a separate network (think about it--each interface is its own subnet), but via the router we are able to communicate between networks
- A few of the ports will use private IP addresses because it's on the LAN
- One of the ports will use a public IP (assigned by the ISP)

You may have some combination devices, e.g. the router and wireless AP are the same device


### (Aside) Private vs. Public IP Addres

Private IP addresses are not routable--you can not use this on the public internet.

Private IP addresses were designed to prevent the exhaustion of IP addresses on the public internet

Imagine a packet has the source and destination IP address, but it's constructed in such a way:

```
[ source        | destination ]
[ 192.168.10.11 |     8.8.8.8 ]
```

The router will drop this because the source IP is private, there is no way for Google to "respond" to the TCP/IP message. In other words, it's theoretically possible to deliver this to google because the destination IP is ok, but the router's understand the packet is malformed.

**NAT (Network Address Translator)**

Translates between public and private IP addresses

## Switched vs. Broadcast Networks

**Switched Network**
- Switch learns which MAC addresses are on which ports
- Sends unicast traffic only to the specific port where the destination device is connected
- More efficient, reduces unnecessary traffic
- Switch recognizes only MAC addresses (it does not deal with IP addresses)
- Each IP address handled on the switch have the same NET-ID (I assume this is subnet)
- The switch does not have its own IP address
- As opposed to the hub, the switch assembles the TCP/IP packet, determines the destination device, and connects them together (the hub just broadcasts all bits to all ports)

**Broadcast Domain** 
- A network segment where broadcast messages reach all devices
- When a device sends to a broadcast address, ALL devices in that domain receive it
- Switches forward broadcast traffic to all ports (except the one it came from)
- Routers typically **block** broadcasts (they don't forward them), so they define the boundary of broadcast domains

**The 255.255.255.255 Address:**
- This is the **limited broadcast address**. When a device sends to this address:
- The packet goes to **every device** on the local network segment
- It does NOT cross routers (stays within the broadcast domain)

**Common uses:**
- **DHCP Discovery**: When your device first connects and doesn't have an IP yet, it broadcasts "Is there a DHCP server?" to 255.255.255.255
- **ARP requests**: "Who has IP address X?" goes to the broadcast MAC address (FF:FF:FF:FF:FF:FF)

**Directed Broadcast:**
- There's also a **directed broadcast** - the last address in a subnet:
- For subnet 192.168.0.0/24, the broadcast address is 192.168.0.255
- Reaches all devices in that specific subnet

## Network Topology


![[Screenshot 2026-01-20 at 12.40.15 PM.png]]
Network topology is the physical arrangement (layout) of the network nodes and the links interconnecting them.

#### Types of Network Topology
- **Mesh topology**
- **Star/Hub topology**
- **Bus topology**
- **Tree topology**
- **Ring topology**

#### Fully Connected Networks

A fully connected network is one in which every node is connected to every other node.

#### Topology Diagrams
- **Bus Topology**: Linear arrangement with nodes connected along a single backbone
- **Ring Topology**: Circular arrangement where each node connects to two adjacent nodes
- **Star Topology**: Central hub with nodes radiating outward
- **Extended Star Topology**: Multiple star configurations interconnected
- **Mesh Topology**: Multiple interconnections between nodes for redundancy


## Link Duplicity
#### Simplex
- **One direction** communication only
- Example: Radio/Television broadcasting
- Data flows in a single direction from sender to receiver
#### Half Duplex (HDX)
- **Either direction, but only one way at a time**
- Communication can go both ways, but not simultaneously
- Example: Police radio
- Devices take turns transmitting and receiving
#### Full Duplex (FDX)
- **Both directions at the same time**
- Simultaneous two-way communication
- Example: Telephony
- Both parties can transmit and receive concurrently

## Transmission Modes

![[Screenshot 2026-01-20 at 12.42.53 PM.png]]



## Physical Media

#### Guided Media
- Contains a physical boundary (copper, fiber, coax)
#### Unguided Media
- No physical boundary, signal is free (radio, wifi, cellular, satellite, etc.)


## The Internet

- Many, many networks belonging to different administrations, entities, etc, **who all agreed to use IP (internet protocol)**

>[!warning] TCP vs. IP
>The "internet" (all routers along the internet) does not see TCP or care what that is -- by the time it reaches them it's all "IP"
>
>You will see below, **IP protocol** does not guarantee packets arrive in order, or at all. Clearly, this gets confusing for practical applications, so **TCP (transmission control protocol) was created**.


>[!info] More on TCP
>
>TCP is only loaded on the end system, not on the router:
>
>**TCP is connection oriented**
>- We do not set up a physical connection
>- The client needs to shake hands with the server before sending
>- You can think of it like a "virtual" or symbolic connection
>- **The client is the one who initiates the hand shaking**
>
>**TCP does not make any guarantees:**
>- delay
>- bandwidth, 
>- throughput performance, etc.
>
>**TCP only guarantees:**
>- accuracy


```
Destination Host
                    
+------------+
|            |             
|    APP     |           
+------------+           
|            |           
|  TCP | UDP |           
+------------+           
|            |           
|    IP      |           
+------------+    

Internet       
```


>[!note] More on UDP
>
>**User Datagram Protocol**
>
>- UDP does not guarantee the application anything
>- If IP passes packets our of order to UDP, UDP just passes it through to the application
>- UDP does not care if the network is congested or not
>- UDP is "reckless", just sends traffic despite congestion, performance, ordering, loss
>- No handshaking, ack, etc.
>- Better for applications that cannot tolerate any delay, "real-time"


- Billions of connected **computing devices**
	- **hosts** = end systems
	- running network apps at the **edge**
- **Packet switches** 
	- Forward packets, e.g. routers, switches
- **Communication links**
	- fiber, copper, radio, satellite
	- transmission rate: bandwidth

- **Protocols** are everywhere
	- control sending and receiving messages
	- protocols do not automatically become standards, there are many protocols that are not adopted everywhere
		- **RFC**: Request for Comments
		- **IETF**: Internet Engineering Task Force
	- HTTP, streaming, Skype, TCP, IP, WiFi, 4G, Ethernet

### Internet: Service View

- Communication Infrastructure enables distributed applications
- Communications services provided to applications include
	- Reliable data delivery from source to destination
	- "Best effort" (unreliable) data delivery

## Network Edge Services (I) - "Reliable Service"

**Goal:** Data transfer between end systems

**Handshaking:** Setup (prepare for) data transfer ahead of time
- Hello, initial establishment
- Set up "state" in two communicating hosts

**TCP - Transmission Control Protocol**
- Internet's reliable data transfer service

**TCP Service:**
- Reliable, in-order byte-stream data transfer
    - Loss: acknowledgements and retransmissions
- Flow control:
    - Sender won't overwhelm receiver
- Congestion control:
    - Senders "slow down sending rate" when network congested


## Network Edge Services (II) - Best Effort "Unreliable" Service

**Goal:** Data transfer between end systems (same as before!)

**UDP - User Datagram Protocol**
- Connectionless
- Unreliable data transfer
- No flow control
- No congestion control

**Apps using TCP:**
- HTTP (Web), FTP (file transfer), Telnet (remote login), SMTP (email)

**Apps using UDP:**
- Streaming media, teleconferencing, DNS, Internet telephony


## Networks Structure

**Edge** – The boundary between the service-provider's premises and the customer's location. The concentration point where large numbers of customer connections will be terminated.

**Aggregation** – A concentration point where data from multiple Edge locations will be funneled.

**Core** – The heart of the network. The major switching locations that form the center of the network, where data from multiple Aggregation sites will be funneled.
- This is typically where one sees the highest volume of data present in the network


## Access Networks

**Key Question:** How do we connect end systems to the edge router?

**Types of Access Networks:**

- Residential Access Networks
- Institutional access networks (school, company)
- Mobile access networks (WiFi, 4G/5G, etc.)

**What to look for when comparing access networks:**

- Bandwidth (bits per second) of access network
- Shared or dedicated access?


### Internet Access: DSL (Digital Subscriber Line)

DSL uses existing telephone infrastructure to provide internet access.

**Architecture:**

- Home equipment: DSL modem → splitter → dedicated phone line to central office
- Central office equipment: DSLAM (DSL Access Multiplexer) separates voice and data traffic
- Voice traffic routes to telephone network; data traffic routes to ISP

**Key characteristics:**

- Voice and data transmitted at different frequencies over a dedicated line to central office
- **Dedicated access** (unlike cable)
- Up to 15-20 Mbps upstream
- Up to 50 Mbps downstream
- Dedicated physical line to telephone central office


### Internet Access: Residential Cable

Cable internet uses the cable TV infrastructure (coaxial cable network).

**Architecture:**

- Home equipment: cable modem → splitter
- Neighborhood homes share connection to cable headend
- Uses HFC (Hybrid Fiber Coax) - fiber to neighborhood, coax to homes

**Key characteristics:**

- **Shared access** (unlike DSL) - bandwidth shared among neighborhood users
- Asymmetric speeds: 40 Mbps to 1 Gbps downstream, 30-100 Mbps upstream
- Uses Frequency Division Multiplexing (FDM): different channels transmitted in different frequency bands
    - Channels allocated for video, data, and control signals

**DSL vs Cable Tradeoff:** DSL offers dedicated bandwidth but typically lower speeds; Cable offers higher potential speeds but shared bandwidth means performance varies with neighborhood usage.


### Internet Access: Home Network

Modern home networks combine multiple technologies to connect devices internally and to the ISP.

**Components:**

- **Cable or DSL modem** - connects to ISP via headend or central office
- **Router/Firewall/NAT** - often combined in single box with wireless access point
- **WiFi wireless access point** - 54 Mbps to 450 Mbps for wireless devices
- **Wired Ethernet** - 1 Gbps for stationary devices

**Connected devices:** laptops, smartphones, desktops, smart appliances (IoT)


### Internet Access: Enterprise Network

Used by companies, universities, and other large institutions.

**Architecture:**

- End systems connect to Ethernet switches
- Switches connect to institutional router
- Router connects to ISP via institutional link
- Often includes institutional mail and web servers

**Key characteristics:**

- Wired: 100 Mbps, 1 Gbps, or 10 Gbps transmission rates
- Wireless: 54 Mbps to 450 Mbps
- Today, end systems typically connect into Ethernet switches (not directly to routers)


### Internet Access: Wireless

Shared wireless access network connects end systems to router via base station (access point).

**Wireless Local Area Networks (WLANs):**

- Typically within or around a building (~100 ft range)
- 802.11b/g/n (WiFi): 11, 54, 450 Mbps transmission rates
- Connects to internet via wired backhaul

**Wide-Area Cellular Access Networks:**

- Provided by mobile/cellular network operators
- Range: 10's of kilometers
- Speeds: 10's of Mbps
- 4G cellular networks (5G emerging)
- Enables mobile internet access anywhere with coverage

**WLAN vs Cellular Tradeoff:** WLANs offer higher speeds but limited range; cellular offers mobility and wide coverage but typically lower speeds and metered data.


### Summary: Access Network Comparison

| Type             | Bandwidth                         | Access Type | Best For                     |
| ---------------- | --------------------------------- | ----------- | ---------------------------- |
| DSL              | Up to 50 Mbps down, 15-20 Mbps up | Dedicated   | Consistent performance needs |
| Cable            | Up to 1 Gbps down, 30-100 Mbps up | Shared      | High bandwidth needs         |
| Enterprise       | 100 Mbps - 10 Gbps                | Dedicated   | Business/institutional use   |
| WLAN (WiFi)      | 11-450 Mbps                       | Shared      | Local wireless mobility      |
| Cellular (4G/5G) | 10's Mbps+                        | Shared      | Wide-area mobility           |

---

## The Core Network

The core network is a mesh of interconnected routers that transfers data between access networks.

**The fundamental question:** How is data transferred through the network?

Two approaches:

- **Circuit Switching** - dedicated circuit per call (telephone network / PSTN)
- **Packet Switching** - data sent in discrete "chunks" called packets, forwarded router to router (Internet)

---

### Circuit Switching

Circuit switching establishes a dedicated communication path between two endpoints for the entire duration of the communication.

**Key characteristics:**

- End-to-end resources reserved for duration of call (used in PSTN)
- Link bandwidth and switch capacity are dedicated
- Dedicated resources with no sharing → predictable performance
- Circuit-like guaranteed performance (High QoS)
- Call setup required before data transfer
- Must re-establish call upon failure

**How it works:** Each link is divided into multiple circuits (using FDM or TDM). When a call is made, it gets assigned specific circuits on each link along the path. These circuits remain reserved even during silence/idle periods.

**Example:** In a network where each link has 4 circuits, a call might get the 2nd circuit on one link and the 1st circuit on the next link - these remain dedicated for the entire call.

**Advantages:**

- Guaranteed bandwidth and QoS
- Predictable, consistent performance
- No congestion once connection established
- Low latency (no queuing delays)

**Disadvantages:**

- Inefficient for bursty data (resources wasted during idle periods)
- Limited number of simultaneous connections
- Call setup delay before communication begins
- Entire path fails if any link fails

---

### Packet Switching

Packet switching breaks data into small packets that are independently routed through the network.

>[!note] Packet Structure
>Each message is split into:
>- **header**: source IP, destination IP (both must be public)
>- **payload**: message content
>.
>- You always need a header for each packet, even if every payload belongs to the same message
>- Routers on the internet do not look at the payload, **only the header**
>	- It's possible the payload is TCP
>	- It's possible the payload is UDP
>	- **The router doesn't care**


```
        ┌──────────────┐                               
        │  MESSAGE     │                               
    ┌───┴───────┬──────┴─────────────────────┐         
    │           │                            │         
┌───┼────────┐  └───┬───┬─────────┐      ┌───┼────────┐
│ H │ PAYLOAD│      │ H │PAYLOAD  │      │ H │PAYLOAD │
└───└────────┘      └───└─────────┘      └───└────────┘
```


**Key characteristics:**

- Mesh of interconnected routers
- Hosts break application-layer messages into packets
- Packets forwarded from one router to the next, across links on path from source to destination
- Each packet transmitted at full link capacity
- Resources used as needed (no reservation)

**How it works:**

- Each end-to-end data stream is divided into packets
- Multiple users (A, B, etc.) share network resources
- Each packet uses full link bandwidth while being transmitted
- No bandwidth division into "pieces," no dedicated allocation, no resource reservation

**Store and Forward:** Packets move one hop at a time. A node must receive the complete packet before forwarding it to the next hop.

**Statistical Multiplexing:** Unlike circuit switching where resources are pre-allocated, packet switching multiplexes packets from different sources dynamically based on demand. This is more efficient when traffic is bursty.

---

### Resource Contention in Packet Switching

Because resources aren't reserved, packet switching faces contention issues:

**Congestion:** Aggregate resource demand can exceed amount available, causing packets to queue and wait for link access.

**Queuing and Loss:**

- If arrival rate (in bps) exceeds transmission rate of link for a period of time:
    - Packets will queue, waiting to be transmitted on the link
    - Packets can be dropped (lost) if the memory buffer fills up

**Example scenario:** Two hosts (A and B) connected via 100 Mb/s Ethernet links to a router, which connects to destinations via a 1.5 Mb/s link. When both hosts send data simultaneously, the combined rate exceeds the output link capacity, causing packets to queue.

---

### Packet vs. Circuit Switching Comparison

**Advantages of Packet Switching:**

- Great for bursty data traffic
- Resource sharing makes it scalable
- Simpler design, no call setup required
- More robust - can re-route around failures

**Disadvantages of Packet Switching:**

- Excessive congestion causes packet delay and loss
- Without admission control, requires protocols for reliable data transfer and congestion control
- Per-packet overhead (each packet needs source/destination addresses, etc.)
- Harder to build applications requiring high QoS (no guaranteed bandwidth)

---

### Numerical Example: Why Packet Switching Wins for Data

**Scenario:**

- 1 Gbps link
- Each user needs 100 Mbps when "active"
- Users are active only 10% of the time

**Circuit Switching:**

- Must reserve 100 Mbps per user
- Maximum users = 1 Gbps / 100 Mbps = **10 users**

**Packet Switching:**

- With 35 users, the probability that more than 10 are active simultaneously is less than **0.0004** (0.04%)
- Calculated using binomial distribution: P(X > 10) where X ~ Binomial(n=35, p=0.1)

**Conclusion:** Packet switching allows more users to share the network because it exploits the statistical nature of bursty traffic. Users rarely all need full bandwidth simultaneously.

---

### Functions of the Core Network

Routers in the core perform two key functions:

**Routing:**

- Determines the source-to-destination route taken by packets
- Uses routing algorithms to compute best paths
- Populates the local forwarding table

**Forwarding:**

- Moving packets from router's input to appropriate router output
- Uses local forwarding table to make per-packet decisions
- Table maps header values (destination addresses) to output links

**How forwarding works:**

1. Packet arrives with destination address in header (e.g., "0111")
2. Router looks up header value in local forwarding table
3. Table indicates which output link to use (e.g., header "0111" → output link 2)
4. Router forwards packet to that output link

**Routing vs Forwarding:**

- Routing is the _global_ process of determining paths (control plane)
- Forwarding is the _local_ action of moving a packet (data plane)

---

### Summary: Circuit vs Packet Switching

|Aspect|Circuit Switching|Packet Switching|
|---|---|---|
|Resource allocation|Dedicated/reserved|Shared/on-demand|
|Setup required|Yes (call setup)|No|
|Bandwidth guarantee|Yes|No|
|Efficiency for bursty data|Poor (wastes idle capacity)|Excellent|
|Congestion|None once connected|Possible (queuing, loss)|
|Failure handling|Re-establish entire call|Re-route individual packets|
|Per-unit overhead|Per-call|Per-packet|
|Scalability|Limited by circuits|Highly scalable|
|Best for|Voice, real-time (traditional)|Data, web, email (Internet)|
|Example|Telephone network (PSTN)|Internet|

**Key insight:** The Internet chose packet switching because data traffic is inherently bursty - users don't need constant bandwidth. By statistically multiplexing many users, packet switching achieves much higher utilization of network resources, even though it sacrifices guaranteed performance.


