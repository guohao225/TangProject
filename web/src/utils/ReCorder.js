class OperationRecords{
    constructor() {
        this.record = []
    }
    addRecord(source,sourceName, target, targetName, type, id, loop){
        this.record.push({source:source,
            sourceName:sourceName,
            target:target,
            targetName:targetName,
            type:type,
            id:id,
            loop:loop,
        })
    }
}

let recorder = new OperationRecords()
export default recorder