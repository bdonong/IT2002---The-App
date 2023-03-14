import { RelationView } from "../App"

interface TableViewProps {
    relationView: RelationView
}

const TableView = (props: TableViewProps) => {
    return (
        <div id="sub-view">
            <p>The view of you relation:</p>
            {
                props.relationView.columns.length > 0 &&
                <table>
                    <tr>
                        {
                            props.relationView.columns.map(col => {
                                return <th>{col}</th>
                            })
                        }
                    </tr>
                    {
                        props.relationView.rows.map(row => {
                            return <tr>
                                {
                                    props.relationView.columns.map(col => {
                                        return <td>{row[col]}</td>
                                    })
                                }
                            </tr>
                        })
                    }


                </table>
            }
        </div>
    )
}

export default TableView