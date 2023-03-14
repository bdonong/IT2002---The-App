import { useState } from "react"

interface FieldRowProps {
    showDelete: boolean
    id: number
    dataTypes: Array<string>
    fieldName: string
    fieldType: string
    onFieldNameEdit: (id: number, fieldName: string) => void
    onFieldTypeEdit: (id: number, fieldType: string) => void
    onFieldAddition: (id: number) => void
    onFieldDeletion: (id: number) => void
}

const FieldRowView = (props: FieldRowProps) => {
    return (
        <div className="horizontal-alignment">
            <div className="horizontal-alignment">
                <p>Field name:&nbsp;</p>
                <input type="text" value={props.fieldName} onChange={handleFieldNameEdit} />
            </div>
            <div className="horizontal-alignment">
                <p>Field type:&nbsp;</p>
                <select name="field-type" id="field-type" defaultValue={props.fieldType} onChange={handleFieldTypeEdit}>
                    {
                        props.dataTypes.map((dataType) => {
                            return <option key={dataType} value={dataType}>{dataType}</option>
                        })
                    }
                </select>
            </div>
            <div className="horizontal-alignment">
                <button onClick={() => { props.onFieldAddition(props.id) }}>+</button>
                <span>&nbsp;&nbsp;</span>
                {
                    props.showDelete &&
                    <button onClick={() => { props.onFieldDeletion(props.id) }}>delete</button>
                }
            </div>
        </div>
    )

    function handleFieldNameEdit(event: React.ChangeEvent<HTMLInputElement>) {
        props.onFieldNameEdit(props.id, event.target.value)
    }

    function handleFieldTypeEdit(event: React.ChangeEvent<HTMLSelectElement>) {
        props.onFieldTypeEdit(props.id, event.target.value)
    }

}

export default FieldRowView