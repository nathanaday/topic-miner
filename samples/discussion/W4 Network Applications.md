# Network Applications: HTTP, SMTP & P2P Networks

**Course:** EE450 — Computer Networks
**Topic:** Discussion Session #4

---

## Popular Network Applications

Network applications span many categories, each relying on specific protocols and architectures:

| Category | Protocol / Technology | Examples |
|---|---|---|
| Email / Messaging | SMTP, IMAP, POP3 | Outlook, Gmail, Thunderbird |
| Web Applications | HTTP / HTTPS | Browsers, web apps |
| Social Networks | HTTP / HTTPS | Facebook, Twitter |
| Search Engines | HTTP / HTTPS | Google, Bing |
| P2P File Sharing | BitTorrent | uTorrent, qBittorrent |
| Online Gaming | Proprietary / UDP | Multiplayer games |
| Video Streaming | HTTP / RTP / RTSP | Netflix, YouTube |
| VoIP | SIP / RTP | Skype, Zoom |
| Cloud Computing | Various | AWS, Azure |

---

## Creating a Network Application

### What You Need to Do

- Write programs for **end systems** (hosts)
- Programs communicate over the network
- Example: Web server ↔ Browser software

### What You DON'T Need

- No software for network-core devices
- Routers and switches don't run user applications
- This separation enables rapid development

### Application Layer Stack

> *Diagram: Two end systems each have all five layers (Application, Transport, Network, Data Link, Physical). The network core only has the bottom three layers (Network, Data Link, Physical). The Application and Transport layers exist only at the end systems.*

| Layer | End System 1 | Network Core | End System 2 |
|---|---|---|---|
| Application | ✔ | — | ✔ |
| Transport | ✔ | — | ✔ |
| Network | ✔ | ✔ | ✔ |
| Data Link | ✔ | ✔ | ✔ |
| Physical | ✔ | ✔ | ✔ |

---

## Process Communication

At the **application layer**, communication happens **process-to-process**, not just computer-to-computer.

A **process** is a program running on a host (computer/server) that enables communication with other processes.

- **Within the same host:** Two processes communicate using **inter-process communication (IPC)**, which is defined by the OS.
- **Across different hosts:** Processes communicate by **exchanging messages** over the network.

> *Diagram: Two hosts each contain a process connected to a socket, which interfaces with TCP buffers and variables. The sockets communicate through the Internet. The process and socket are controlled by the application developer, while TCP and lower layers are controlled by the operating system.*

---

## Process Communication & Sockets

### Process Types

- **Client Process:** Initiates communication
- **Server Process:** Waits to be contacted
- **P2P applications** have both client AND server processes!

### What is a Socket?

- Interface between the **application layer** and the **transport layer**
- Acts like a "door" for messages
- Identified by: **IP Address + Port Number**
  - Example: `192.168.1.5:50500` → `142.250.72.206:443`

> *Diagram: Socket Communication Model — Two Application Processes each have a Socket that connects down to the Transport Layer. The two sides communicate through the Internet.*

---

## Application-Layer Protocol Defines

An application-layer protocol specifies the following:

1. **Types of Messages Exchanged** — Request and response messages; control and data messages
2. **Message Syntax** — What fields are in messages; how fields are delineated
3. **Message Semantics** — Meaning and interpretation of information in fields
4. **Rules & Procedures** — When processes send messages; how processes respond to messages

### Open Protocols (Public)

- **Defined in RFCs** — Everyone has access to the protocol definition
- **Allows for interoperability** — Different implementations can communicate
- **Examples:** HTTP, SMTP, DNS, FTP

### Proprietary Protocols (Private)

- **Controlled by organizations** — Specifications not publicly available
- **Limited interoperability** — Usually work only with specific software
- **Examples:** Skype, Discord, proprietary gaming protocols

---

## Application Layer Protocols Overview

Different tasks require different protocols:

| Protocol | Full Name | Task | Why This Protocol? |
|---|---|---|---|
| **HTTP** | HyperText Transfer Protocol | Web Browsing — viewing websites, clicking links, submitting forms | Stateless request-response model, perfect for retrieving web pages quickly |
| **SMTP** | Simple Mail Transfer Protocol | Email Delivery — sending emails between mail servers | Reliable delivery with store-and-forward mechanism, handles queuing and retries |
| **FTP** | File Transfer Protocol | File Transfer — uploading/downloading large files, managing directories | Separate control & data channels, supports resume, directory navigation |
| **DNS** | Domain Name System | Name Resolution — converting domain names to IP addresses | Extremely fast lookup with hierarchical caching, uses UDP for speed |
| **HTTPS** | HTTP Secure | Secure Web Transactions — online banking, shopping, sensitive data | Encryption with TLS/SSL ensures data privacy and authentication |
| **RTP/RTSP** | Real-time Transport Protocol | Video/Audio Streaming — live streaming, video conferencing, VoIP | Prioritizes low latency over perfect delivery, timestamps for synchronization |

---

## Internet Transport Protocol Services

| Feature | TCP (Transmission Control Protocol) | UDP (User Datagram Protocol) |
|---|---|---|
| **Reliability** | ✔ Reliable data transfer guaranteed | ✘ Unreliable, packets may be lost |
| **Flow Control** | ✔ Prevents overwhelming receiver | ✘ No flow control |
| **Congestion Control** | ✔ Throttles when network overloaded | ✘ No congestion control |
| **Connection** | ✔ Connection-oriented (setup required) | ✘ Connectionless |
| **Speed** | Slower (due to overhead) | Faster (minimal overhead) |
| **Use Cases** | Web browsing, Email, File transfer | Video streaming, Gaming, DNS |

---

## HTTP (HyperText Transfer Protocol)

### Key Characteristics

- Web's **application layer** protocol
- **Client/Server** model
- Uses **TCP on port 80**
- **Stateless** — no memory of past requests

### Web Page Components

- **Base HTML file**
- **Referenced objects** (images, CSS, JS)
- Each object has a **URL**
- Example: `www.site.com/path/file.jpg`

### HTTP Request/Response Flow

> *Diagram: A browser (client process, e.g., Firefox or Chrome) sends an HTTP Request to a Web Server (e.g., Apache, Nginx). The Web Server sends back an HTTP Response.*

---

## HTTP Overview (Continued)

### Uses TCP

1. **Client initiates TCP connection** (creates socket to server, **port 80**)
2. **Server accepts TCP connection** from client
3. **HTTP messages** (application-layer protocol messages) exchanged between browser (HTTP client) and Web server (HTTP server)
4. **TCP connection closed**

### HTTP is "Stateless"

- Server maintains **no information** about past client requests

### Why Stateless?

- Protocols that maintain "state" are **complex**:
  - Past history (state) must be maintained
  - If server/client crashes, their views of "state" may be inconsistent and must be reconciled
  - Example: An Online Banking App must carefully manage state

---

## HTTP Connection Types

### Non-Persistent HTTP

- **One object** per TCP connection
- Connection **closed after each object**
- Requires **multiple connections** for multiple objects

### Persistent HTTP

- **Multiple objects** over a single TCP connection
- Server **keeps connection open**
- **Reduces overhead** significantly

> *Diagram: Non-persistent connections show repeated OPEN/CLOSE cycles for each object. Persistent connections show a single OPEN at the start, multiple request/response exchanges, then a single CLOSE at the end.*

---

## Non-Persistent HTTP: Response Time

### Definition of RTT

**RTT (Round-Trip Time):** Time for a small packet to travel from client to server and back.

### Response Time Breakdown

- **1 RTT** to initiate TCP connection
- **1 RTT** for HTTP request and first few bytes of HTTP response to return
- **File transmission time**

**Total = 2 RTT + transmit time** (per object)

> *Diagram: Timeline showing client initiating TCP connection (1 RTT), then sending request and receiving file (1 RTT + transmit time). Total time from start to file received = 2 RTT + file transmission time.*

---

## Non-Persistent HTTP: Step-by-Step Example

Suppose user enters URL: `www.someSchool.edu/someDepartment/home.index`
(The page contains text and references to 10 JPEG images)

1. **1a.** HTTP client initiates TCP connection to HTTP server at `www.someSchool.edu` on port 80
2. **1b.** HTTP server at host is waiting for TCP connection at port 80. It "accepts" the connection, notifying client
3. **2.** HTTP client sends HTTP request message (containing URL) into TCP connection socket. Message indicates client wants object `someDepartment/home.index`
4. **3.** HTTP server receives request, forms response message containing the requested object, and sends it into its socket
5. **4.** HTTP server closes TCP connection
6. **5.** HTTP client receives response message containing the HTML file, displays HTML. Parsing the HTML file, it finds 10 referenced JPEG objects
7. **6.** Steps 1–5 are repeated for each of the 10 JPEG objects

---

## Variations of HTTP

### Non-Persistent Connections

- **With serial connections** — one connection at a time
- **With parallel connections** — multiple simultaneous connections

### Persistent Connections

- **Without pipelining** — wait for response before sending next request
- **With pipelining** — send multiple requests back-to-back without waiting

### RTT Comparison (HTML page with 2 image objects)

| Variation | Time Delay (in RTTs) | Explanation |
|---|---|---|
| Non-Persistent, Serial | **6 RTTs** | 2 RTTs per object × 3 objects (HTML + 2 images) |
| Non-Persistent, Parallel | **4 RTTs** | 2 RTTs for HTML, then 2 RTTs for both images simultaneously |
| Persistent without Pipelining | **4 RTTs** | 1 RTT for connection + 1 RTT for HTML + 1 RTT for image 1 + 1 RTT for image 2 |
| Persistent with Pipelining | **3 RTTs** | 1 RTT for connection + 1 RTT for HTML + 1 RTT for both images (pipelined) |

> *Diagrams: Four timing diagrams showing the different connection strategies. Each shows the client-server exchange with color-coded delays: gray for connection handshake, green for HTML page request, orange for object request.*

---

## HTTP Request Message

### Structure

There are **two types of HTTP messages: request and response.**

HTTP request messages are in **ASCII** (human-readable format).

An HTTP request message contains:

- **Request line** — method, URL, HTTP version (e.g., `GET /index.html HTTP/1.1`)
- **Header lines** — additional request information (Host, User-Agent, Accept, etc.)
- **Carriage return / line feed** — blank line indicates end of header lines (`\r\n`)
- **Body** (optional, used with POST)

### Common HTTP Methods

| Method | Purpose |
|---|---|
| **GET** | Retrieve a page/resource from the server |
| **POST** | Send data to the server (like a form submission) |
| **HEAD** | Same as GET but returns only headers (no body) |

### Example HTTP Request

```
GET /index.html HTTP/1.1\r\n
Host: www-net.cs.umass.edu\r\n
User-Agent: Firefox/3.6.10\r\n
Accept: text/html,application/xhtml+xml\r\n
Accept-Language: en-us,en;q=0.5\r\n
Accept-Encoding: gzip,deflate\r\n
Accept-Charset: ISO-8859-1,utf-8;q=0.7\r\n
Keep-Alive: 115\r\n
Connection: keep-alive\r\n
\r\n
```

---

## HTTP Response Message

### Structure

An HTTP response message contains:

- **Status line** — protocol version, status code, status phrase (e.g., `HTTP/1.1 200 OK`)
- **Header lines** — response metadata and server info (Date, Server, Content-Type, etc.)
- **Data** — the requested content (e.g., HTML file)

### Example HTTP Response

```
HTTP/1.1 200 OK\r\n
Date: Sun, 26 Sep 2010 20:09:20 GMT\r\n
Server: Apache/2.0.52 (CentOS)\r\n
Last-Modified: Tue, 30 Oct 2007 17:00:02 GMT\r\n
ETag: "17dc6-a5c-bf716880"\r\n
Accept-Ranges: bytes\r\n
Content-Length: 2652\r\n
Keep-Alive: timeout=10, max=100\r\n
Connection: Keep-Alive\r\n
Content-Type: text/html; charset=ISO-8859-1\r\n
\r\n
(Response Body — data data data ...)
```

---

## HTTP Response Status Codes

Status code appears in the **1st line** of the server → client response message.

| Status Code | Meaning | Description |
|---|---|---|
| **200 OK** | Success | Request succeeded; requested object is in this message |
| **301 Moved Permanently** | Redirect | Requested object moved; new location specified in `Location:` header |
| **400 Bad Request** | Client Error | Request message not understood by server |
| **404 Not Found** | Client Error | Requested document not found on this server |
| **505 HTTP Version Not Supported** | Server Error | Server does not support the HTTP version used in the request |

---

## Web Caching (Proxy Servers)

**Goal:** Satisfy client requests **without involving the origin server.**

### How It Works

1. User configures browser to point to a **web cache** (proxy server)
2. Browser sends **all HTTP requests to the cache**
   - **If object is in cache:** Cache returns object to client directly
   - **If object is NOT in cache:** Cache requests object from origin server, caches the received object, then returns it to client

> *Diagram: Clients send HTTP requests to a proxy server. The proxy either responds from its cache or forwards the request to origin servers on the public Internet. A separate diagram shows an institutional network with a 1 Gbps LAN connected via a 1.54 Mbps access link to the public Internet, with and without a local web cache.*

---

## Web Caches (Proxy Servers): Details

### What is a Web Cache?

**Dual Role** — A web cache acts as both:

- **Server** for the original requesting client
- **Client** to the origin server

### Where Are Caches Installed?

Typically installed by an **ISP** (university, company, residential ISP).

### Why Web Caching?

| Benefit | Explanation |
|---|---|
| **Reduce Response Time** | Cache is closer to client, so responses arrive faster |
| **Reduce Traffic** | Less traffic on an institution's access link to the Internet |
| **Internet Efficiency** | Internet is dense with caches; enables smaller content providers to deliver content more effectively |

---

## Electronic Mail System

### Three Major Components

| Component | Role | Examples |
|---|---|---|
| **User Agents** | Composing, editing, reading mail messages | Outlook, Gmail, Thunderbird |
| **Mail Servers** | Store and forward messages | Exchange, Postfix |
| **SMTP Protocol** | Transfer protocol between mail servers | Simple Mail Transfer Protocol |

### User Agent

- Also known as "mail reader"
- Used for composing, editing, and reading mail messages
- Examples: Outlook, elm, Mozilla Thunderbird, iPhone mail client
- Outgoing and incoming messages are stored on the server

> *Diagram: Multiple user agents connect to their respective mail servers. Mail servers communicate with each other using SMTP. Each mail server has an outgoing message queue and user mailboxes.*

---

## Mail Servers

- **Mailbox** contains incoming messages for each user
- **Message queue** holds outgoing (to be sent) mail messages
- **SMTP protocol** is used between mail servers to send email messages
  - **Client role:** The sending mail server
  - **Server role:** The receiving mail server

> *Diagram: Three mail servers connected via SMTP, each with user agents. Arrows show SMTP connections between the servers for message delivery.*

---

## SMTP Protocol

- Uses **TCP** to reliably transfer email from client to server, **port 25**
- **Direct transfer:** sending server to receiving server (no intermediate mail servers)
- **Three phases of transfer:**
  1. Handshaking (greeting)
  2. Transfer of messages
  3. Closure
- **Command/response interaction:**
  - Commands: ASCII text
  - Response: status code and phrase
- **Messages must be in 7-bit ASCII**

---

## Email Access Protocols

**SMTP delivers to the server, but how do we retrieve mail?**

| Protocol | Features | Use Cases |
|---|---|---|
| **POP3** (Post Office Protocol) | Download and delete from server; simple protocol; offline reading; single device access | Single device email access |
| **IMAP** (Internet Mail Access Protocol) | Emails stay on server; folder organization; multi-device sync; search capabilities | Multiple device access, modern email |
| **HTTP** (Web-based) | Browser access; no client software needed; platform independent; rich web interface | Gmail, Yahoo Mail, Outlook.com |

---

## Scenario: Alice Sends a Message to Bob

Step-by-step email delivery process:

1. **Alice** uses her User Agent (UA) to compose a message addressed "to" `bob@someschool.edu`
2. Alice's UA sends the message to **her mail server**; the message is placed in the **message queue**
3. The **client side of SMTP** on Alice's mail server opens a **TCP connection** with Bob's mail server
4. The **SMTP client** sends Alice's message over the TCP connection
5. **Bob's mail server** places the message in **Bob's mailbox**
6. **Bob** invokes his user agent to **read the message**

> *Diagram: Alice (user agent) → her mail server (message queued, SMTP client opens connection) → Bob's mail server (message placed in mailbox) → Bob (user agent reads message).*
