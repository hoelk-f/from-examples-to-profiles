FROM maven:3.9.11-eclipse-temurin-21-alpine AS compiler
WORKDIR /src
COPY lib ./lib
COPY native-classes ./native-classes
COPY RunAdapter.java ./RunAdapter.java
RUN mkdir /classes && javac -cp 'native-classes:lib/*' -d /classes RunAdapter.java
FROM behavioral-testing/qualification-bustle:20261003
COPY --from=compiler /classes /opt/bustle/classes
ENTRYPOINT ["java","-Xmx3g","-XX:ActiveProcessorCount=2","-Djava.util.concurrent.ForkJoinPool.common.parallelism=2","-cp","/opt/bustle/classes:/opt/bustle/lib/*","com.googleresearch.bustle.RunAdapter"]
