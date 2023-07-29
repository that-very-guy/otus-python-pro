# HW-04: Web Server


### Architecture

* Thread pool

### Benchmark

#### ab:
```
Server Software:        OTUServer
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        206 bytes

Concurrency Level:      100
Time taken for tests:   11.874 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      18300000 bytes
HTML transferred:       10300000 bytes
Requests per second:    4210.86 [#/sec] (mean)
Time per request:       23.748 [ms] (mean)
Time per request:       0.237 [ms] (mean, across all concurrent requests)
Transfer rate:          1505.06 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.3      0       1
Processing:     2   19   2.3     19      41
Waiting:        0   14   3.5     14      39
Total:          2   20   2.3     19      41

Percentage of the requests served within a certain time (ms)
  50%     19
  66%     20
  75%     20
  80%     20
  90%     21
  95%     24
  98%     27
  99%     28
 100%     41 (longest request)
```
