from edna.core.execution.context import SimpleStreamingContext
from edna.serializers import KafkaStringSerializer
from edna.ingest.streaming import KafkaIngest
from edna.process import BaseProcess
from edna.emit import KafkaEmit


def main():
    context = SimpleStreamingContext()
    ingestSerializer = KafkaStringSerializer()
    emitSerializer = KafkaStringSerializer()

    ingest = KafkaIngest(serializer=ingestSerializer, 
        kafka_topic=context.getVariable("import_key"),
        bootstrap_server=context.getVariable("bootstrap_server"), 
        bootstrap_port=context.getVariable("bootstrap_port"))
    process = BaseProcess()
    emit = KafkaEmit(serializer=emitSerializer, 
        kafka_topic=context.getVariable("export_key"),
        bootstrap_server=context.getVariable("bootstrap_server"),
        bootstrap_port=context.getVariable("bootstrap_port"))

    context.addIngest(ingest=ingest)
    context.addEmit(emit=emit)
    context.addProcess(process=process)

    context.execute()


if __name__ == "__main__":
    main()