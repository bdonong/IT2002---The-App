import React, { useState } from "react"
import FieldRowView from "./FieldRowView"
import * as api from '../api'
import { RelationView } from "../App"

// ? A custom `type` in TypeScript - defining a map (just as Python dictionaries), whose keys and values are both strings
export type StringMap = { [dtype: string]: string }


// ? Another interface (type) for the exchanged field/row in the relation
interface FieldRow {
    id: number
    // ? field name and type are dynamic in this case, allowing you to freely chose what you want to design
    fieldName: string
    fieldType: string
}

// ? The necessary interface to define the type of the props of the EditView element 
interface EditViewProps {
    // ? Takes RelationView from the parent to interactively modify
    relationView: RelationView
    // ? Used to call the parent component (App in this case) every time something is updated to view it on the right side
    onRelationChange: (relationView: RelationView) => void
}

export const DataTypes: StringMap = {
    'boolean': 'BOOL',
    'integer': 'INT',
    'text': 'TEXT',
    'time': 'TIME',
}

// ? Definition of the component EditView - note that the const `EditView` is a function definiton and it is recognized as an object in runtime
const EditView = (props: EditViewProps) => {
    // ? 4 primitive data types used in definition. Note that all of them are sent to back as strings. You may try to write error-tolerant code in the backend to store them in respective PostgreSQL types
    // ! You will have to add more data types as needed in your table definitions following the below pattern


    // ? A JavaScript way of taking the keys of the above StringMap. It will return the list ['boolean','integer',...]
    const fieldTypes = Object.keys(DataTypes)

    // ? A boolean STATE VARIABLE used to show/hide the user definition (left) and table view (right) windows 
    const [showDefinitionField, setShowDefinitionField] = useState<boolean>(true)


    // ? Is a state variable - an array of FieldRow objects, used to store the added data fields one by one by the user during relation definition
    const [fieldRows, setFieldRows] = useState<Array<FieldRow>>([
        {
            id: 1,
            fieldName: "",
            fieldType: fieldTypes[0],
        }
    ])

    // ? A state variable to store the typed value into the relation name field
    const [relationName, setRelationName] = useState<string>("")
    // ? First it might seem difficult to understand, imagine it this way:
    // ? After you create a relation, you will receive a table view on the right and one of the fields on the left will change
    // ? One of them will allow you to insert values into the responding fields. insertionValues is a StringMap storing those values-to-insert until you press the insert button
    const [insertionValues, setInsertionValues] = useState<StringMap>({})
    // ? The same as above, the StringMap below stores the values for rows to update, and has just one additional parameter, id, to refer to a specific entry
    const [updateValues, setUpdateValues] = useState<StringMap>({})
    // ? ID of the entry/row to be deleted from the relation
    const [deletionId, setDeletionId] = useState<number>(-1)
    return (
        // ? sub-view is the style class used to separate 2 main views - editing and table view
        <div id="sub-view">
            {
                // ? In React JSX elements, if you have a boolean value equal to `false` before the && operator, the element coming after it won't be displayed. Usually used this way to control what to display/hide
                showDefinitionField &&
                // ? NOTE: All the below classNames are given for styling purposes. Refer to the App.scss file to see/modify them
                <div className="relation-definition">
                    <p>Define your relation here:</p>
                    <div className="relation-name">
                        <p>Relation name:&nbsp;</p>
                        {/* As you edit the string inside the Relation name field, the handleRelationNameChange function updates relationName state variable, and*/}
                        <input type="text" value={relationName} onChange={handleRelationNameChange} />
                    </div>

                    <div className="field-rows">
                        {
                            // ? Map method returns an array of components in this case. You can see that each fieldRow element inside the fieldRows state variable is uniquely represented by an id
                            // ? Refer to each method for onField... to know more about what they do
                            fieldRows.map(fieldRow => (
                                <FieldRowView
                                    // ? Below 3 field are for the 3 characteristics of the field definition
                                    id={fieldRow.id}
                                    fieldName={fieldRow.fieldName}
                                    fieldType={fieldRow.fieldType}
                                    onFieldNameEdit={handleFieldNameEdit}
                                    onFieldTypeEdit={handleFieldTypeEdit}
                                    onFieldAddition={handleFieldRowAddition}
                                    onFieldDeletion={handleFieldRowDeletion}
                                    // ? Prevents showing the delete button if there are less than 2 elements to display
                                    showDelete={fieldRows.length > 1}
                                    dataTypes={fieldTypes}
                                    key={fieldRow.id}
                                />
                            ))
                        }
                    </div>
                    <div className="create-relation-button">
                        <button onClick={hanldeRelationCreation}>Create Relation</button>
                    </div>
                </div>
            }
            {
                // ? The same logic as above for the following variable, reverted in this case
                !showDefinitionField &&
                <div className="relation-edition">
                    <div className="value-insertion">
                        <p>Use the below fields to insert an entry:</p>
                        {
                            props.relationView.columns.map(col => {
                                if (col !== "id") {
                                    return (
                                        <div className="row-value" key={col}>
                                            <p>{col}:&nbsp;</p>
                                            <input
                                                type="text"
                                                value={insertionValues[col]}
                                                onChange={(event) => {
                                                    handleInsertionValueEdit(event, col)
                                                }}
                                            />
                                        </div>
                                    )
                                }
                            })
                        }
                        <button onClick={handleEntryInsertion}>Insert Entry</button>
                    </div>
                    <div className="value-modification">
                        <p>Use the below fields to modify an existing entry:</p>
                        {
                            props.relationView.columns.map(col => {
                                return (
                                    <div className="row-value" key={col}>
                                        <p>{col}:&nbsp;</p>
                                        <input
                                            type="text"
                                            value={updateValues[col]}
                                            onChange={(event) => {
                                                handleUpdateValueEdit(event, col)
                                            }}
                                        />
                                    </div>
                                )
                            })
                        }
                        <button onClick={handleEntryUpdate}>Update Entry</button>
                    </div>
                    <div className="value-deletion">
                        <p>Insert the row id to be removed from the relation: </p>
                        <div>
                            <input type="text" onChange={(event) => {
                                handleDeleteValueEdit(event)
                            }} />
                            <button onClick={handleEntryDeletion}>Remove</button>
                        </div>
                    </div>
                </div>
            }
        </div>
    )

    function handleFieldRowAddition(id: number) {
        let _fieldRows = [...fieldRows]
        let idx = _fieldRows.findIndex(fieldRow => fieldRow.id === id)
        let newId = _fieldRows.length + 1
        let newRow: FieldRow = {
            fieldName: "",
            fieldType: fieldTypes[0],
            id: newId
        }
        _fieldRows.splice(idx + 1, 0, newRow)
        setFieldRows(_fieldRows)
    }


    function handleFieldRowDeletion(id: number) {
        let _fieldRows = [...fieldRows]
        let idx = _fieldRows.findIndex(fieldRow => fieldRow.id === id)
        _fieldRows.splice(idx, 1)
        setFieldRows(_fieldRows)
    }

    function handleFieldNameEdit(id: number, fieldName: string) {
        let _fieldRows = [...fieldRows]
        let idx = _fieldRows.findIndex(fieldRow => fieldRow.id === id)
        _fieldRows[idx].fieldName = fieldName

        setFieldRows(_fieldRows)
    }

    function handleFieldTypeEdit(id: number, fieldType: string) {
        let _fieldRows = [...fieldRows]
        let idx = _fieldRows.findIndex(fieldRow => fieldRow.id === id)
        _fieldRows[idx].fieldType = fieldType

        setFieldRows(_fieldRows)

    }

    function handleRelationNameChange(event: React.ChangeEvent<HTMLInputElement>) {
        setRelationName(event.target.value)
    }

    function handleInsertionValueEdit(event: React.ChangeEvent<HTMLInputElement>, col: string) {
        let _insertionValues = { ...insertionValues }
        _insertionValues[col] = event.target.value
        setInsertionValues(_insertionValues)
    }

    function handleUpdateValueEdit(event: React.ChangeEvent<HTMLInputElement>, col: string) {
        let _updateValues = { ...updateValues }
        _updateValues[col] = event.target.value
        setUpdateValues(_updateValues)
    }

    async function hanldeRelationCreation() {
        let body: { [name: string]: string } = {}

        fieldRows.forEach(fieldRow => {
            if (fieldRow.fieldName === "") {
                fieldRow.fieldName = "no_name"
            }
            body[fieldRow.fieldName] = DataTypes[fieldRow.fieldType]
        }
        )

        let relation = {
            name: relationName,
            body: body
        }

        await api.createRelation(relation)

        let submittedRelation = await api.getRelation(relationName)

        //? Updating states for edit and add fields
        let _insertionValues: StringMap = {}
        let _updateValues: StringMap = {}
        submittedRelation.columns.forEach(col => {
            if (col !== "id")
                _insertionValues[col] = ""

            _updateValues[col] = ""
        })
        setInsertionValues(_insertionValues)
        setUpdateValues(_updateValues)


        props.onRelationChange(submittedRelation)
        setShowDefinitionField(false)
    }

    async function handleEntryInsertion() {
        let valueTypes: StringMap = {}
        for (let key of Object.keys(insertionValues)) {
            let fieldValue = fieldRows.find(row => row.fieldName == key)
            if (fieldValue) {
                valueTypes[key] = DataTypes[fieldValue.fieldType]
            }
        }

        let insertionData = {
            name: relationName,
            body: insertionValues,
            valueTypes: valueTypes
        }
        let success = await api.insertEntry(insertionData)
        if (!success) {
            return
        }
        let latestRelation = await api.getRelation(relationName)
        props.onRelationChange(latestRelation)
    }

    async function handleEntryUpdate() {
        let updateData = {
            name: relationName,
            body: updateValues,
            id: updateValues.id
        }
        let success = await api.updateEntry(updateData)
        if (!success) {
            return
        }
        let latestRelation = await api.getRelation(relationName)
        props.onRelationChange(latestRelation)
    }

    async function handleEntryDeletion() {
        let deletionData = {
            relationName,
            deletionId
        }
        let success = await api.deleteEntry(deletionData)
        if (!success) {
            return
        }
        let latestRelation = await api.getRelation(relationName)
        props.onRelationChange(latestRelation)
    }

    function handleDeleteValueEdit(event: React.ChangeEvent<HTMLInputElement>) {
        let _deletionId = parseInt(event.currentTarget.value)
        setDeletionId(_deletionId)
    }


}

export default EditView