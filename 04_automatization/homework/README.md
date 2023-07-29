# HW-04: Web Server


### Architecture

* Thread pool

### Benchmark (apache benchmark)

#### 1 thread:
```
Server Software:        OTUServer
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        206 bytes

Concurrency Level:      100
Time taken for tests:   759.213 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      18300000 bytes
HTML transferred:       10300000 bytes
Requests per second:    65.86 [#/sec] (mean)
Time per request:       1518.425 [ms] (mean)
Time per request:       15.184 [ms] (mean, across all concurrent requests)
Transfer rate:          23.54 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   15  85.8      0     574
Processing:     5 1496 1616.0   1045    8230
Waiting:        1 1121 1350.7    531    7716
Total:          5 1511 1627.5   1045    8231

Percentage of the requests served within a certain time (ms)
  50%   1045
  66%   2064
  75%   2580
  80%   3080
  90%   4098
  95%   4634
  98%   5636
  99%   6133
 100%   8231 (longest request)
```

#### 2 threads:
```
Time taken for tests:   37.362 seconds
Complete requests:      50000
Failed requests:        0
Requests per second:    1338.25 [#/sec] (mean)
Time per request:       74.724 [ms] (mean)
Time per request:       0.747 [ms] (mean, across all concurrent requests)
Transfer rate:          478.32 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    1  16.0      0     520
Processing:     1   70 202.9     19    1581
Waiting:        1   52 172.9     15    1573
Total:          2   70 204.1     19    1582

Percentage of the requests served within a certain time (ms)
  50%     19
  66%     21
  75%     22
  80%     23
  90%     25
  95%    537
  98%   1041
  99%   1057
 100%   1582 (longest request)
```

#### 42 threads (best):
```
Time taken for tests:   11.874 seconds
Complete requests:      50000
Failed requests:        0
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

#### 100 threads:
```
Time taken for tests:   13.144 seconds
Complete requests:      50000
Requests per second:    3803.88 [#/sec] (mean)
Time per request:       26.289 [ms] (mean)
Time per request:       0.263 [ms] (mean, across all concurrent requests)
Transfer rate:          1359.59 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.4      0       6
Processing:     4   22   4.1     20      48
Waiting:        1   16   4.9     16      41
Total:          4   22   4.2     21      48

Percentage of the requests served within a certain time (ms)
  50%     21
  66%     23
  75%     24
  80%     25
  90%     28
  95%     31
  98%     34
  99%     36
 100%     48 (longest request)
```
