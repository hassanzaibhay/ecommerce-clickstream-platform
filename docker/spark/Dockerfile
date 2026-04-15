FROM bitnamilegacy/spark:3.5.6

# Bitnami spark runs as uid 1001 (gid 0), but the image ships without a
# /etc/passwd entry for that uid.  Hadoop's UnixLoginModule calls getpwuid()
# via JNI; if the uid has no passwd entry the call returns null and Spark
# crashes with "NullPointerException: invalid null input: name" before any
# -Duser.name JVM flag can take effect.
#
# Fix: add the entry once at image build time so every JVM that starts inside
# this container can resolve the username without any runtime tricks.
USER root
RUN echo 'spark:x:1001:0:Spark:/tmp:/bin/bash' >> /etc/passwd
USER 1001
