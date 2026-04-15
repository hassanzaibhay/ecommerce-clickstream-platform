FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HADOOP_VERSION=3.4.1
ENV HADOOP_HOME=/opt/hadoop
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
ENV HDFS_NAMENODE_USER=hadoop
ENV HDFS_DATANODE_USER=hadoop
ENV HDFS_SECONDARYNAMENODE_USER=hadoop
ENV YARN_RESOURCEMANAGER_USER=hadoop
ENV YARN_NODEMANAGER_USER=hadoop

# Layer 1: OS packages (cached until ubuntu:22.04 changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-11-jdk-headless \
    python3 \
    python3-pip \
    curl \
    ssh \
    rsync \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Layer 2: Create user (cached)
RUN groupadd -g 1000 hadoop && \
    useradd -u 1000 -g hadoop -m -s /bin/bash hadoop

# Layer 3: Download Hadoop (cached as long as VERSION doesn't change)
RUN curl -fsSL https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
    | tar -xz -C /opt \
    && mv /opt/hadoop-${HADOOP_VERSION} ${HADOOP_HOME} \
    && rm -rf ${HADOOP_HOME}/share/doc \
    && chown -R hadoop:hadoop ${HADOOP_HOME}

# Layer 4: Config files (only invalidates when XMLs change)
COPY docker/hadoop/core-site.xml ${HADOOP_HOME}/etc/hadoop/core-site.xml
COPY docker/hadoop/hdfs-site.xml ${HADOOP_HOME}/etc/hadoop/hdfs-site.xml
COPY docker/hadoop/yarn-site.xml ${HADOOP_HOME}/etc/hadoop/yarn-site.xml
COPY docker/hadoop/mapred-site.xml ${HADOOP_HOME}/etc/hadoop/mapred-site.xml

# Layer 5: MapReduce scripts (only invalidates when scripts change)
COPY hadoop/mapreduce /opt/hadoop/mapreduce
RUN chmod +x /opt/hadoop/mapreduce/category_events/mapper.py \
             /opt/hadoop/mapreduce/category_events/reducer.py \
             /opt/hadoop/mapreduce/brand_revenue/mapper.py \
             /opt/hadoop/mapreduce/brand_revenue/reducer.py \
    && chown -R hadoop:hadoop /opt/hadoop/mapreduce

USER hadoop
WORKDIR ${HADOOP_HOME}
