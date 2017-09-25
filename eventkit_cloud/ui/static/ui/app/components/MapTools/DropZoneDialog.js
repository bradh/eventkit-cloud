import React, {Component, PropTypes} from 'react';
import PopupBox from '../PopupBox';
import RaisedButton from 'material-ui/RaisedButton';
import BaseDialog from '../BaseDialog';
import FileFileUpload from 'material-ui/svg-icons/file/file-upload';
const Dropzone = require('react-dropzone');

export class DropZoneDialog extends Component {

    constructor(props) {
        super(props);
        this.onDrop = this.onDrop.bind(this);
        this.onOpenClick = this.onOpenClick.bind(this);
        this.handleClear = this.handleClear.bind(this);
    }

    onDrop(acceptedFiles) {
        if(acceptedFiles.length == 1) {
            const file = acceptedFiles[0];
            this.props.setImportModalState(false);
            this.props.processGeoJSONFile(file);
        }
    }

    onOpenClick() {
        this.dropzone.open();
    }

    handleClear() {
        this.props.setImportModalState(false);
        this.props.setAllButtonsDefault();
    }
    
    render() {
        const styles = {
            drop: {
                margin: '0px auto',
                width: '100%',
                height: '200px',
                textAlign: 'center',
                border: '1px dashed',
                fontSize: '1em',
                color: '#4498c0'
            },
            text: {
                verticalAlign: 'center',
                color: 'grey',
                height: '100px',
                marginTop: '50px'
            }
        }

        return(
            <BaseDialog
                show={this.props.showImportModal}
                onClose={this.handleClear}
                title={'Import AOI'}
                actions={[]}
                bodyStyle={{paddingBottom: '50px'}}
                className={'qa-DropZoneDialog-BaseDialog'}
            >
                <Dropzone 
                    onDrop={this.onDrop} 
                    multiple={false} 
                    style={styles.drop}
                    ref={(node) => {this.dropzone = node;}} 
                    disableClick={true}
                    maxSize={2000000}
                    className={'qa-DropZoneDialog-Dropzone'}
                >
                    <div style={styles.text} className={'qa-DropZoneDialog-text'}>
                        <span><strong>GeoJSON</strong> format only, <strong>2MB</strong> max,<br/>Drag and drop or<br/></span>
                        <RaisedButton
                            style={{margin: '15px 5px 10px'}}
                            labelStyle={{color: 'whitesmoke'}}
                            backgroundColor={'#4598bf'}
                            label={'Select A File'}
                            icon={<FileFileUpload/>}
                            onClick={this.onOpenClick}
                            className={'qa-DropZoneDialog-RaisedButton-select'}
                        />
                    </div>
                </Dropzone>
            </BaseDialog>
        )
    }
}

DropZoneDialog.propTypes = {
    showImportModal: PropTypes.bool,
    setAllButtonsDefault: PropTypes.func,
    setImportModalState: PropTypes.func,
    processGeoJSONFile: PropTypes.func,
}

export default DropZoneDialog;
