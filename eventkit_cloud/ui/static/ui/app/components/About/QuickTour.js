import React, { Component } from 'react';
import PropTypes from 'prop-types';
import QuickTourSection from './QuickTourSection';

export class QuickTour extends Component {

    constructor(props) {
        super(props);
    };

    render() {
        return (
            <div style={{...this.props.containerStyle}} className={'qa-QuickTour-header'}>
                <h4><strong>{this.props.header}</strong></h4>
                {this.props.tourSections.map((section, ix) => {
                    return (
                        <QuickTourSection 
                            key={ix}
                            steps={section.steps}
                            sectionTitle={section.sectionTitle}
                        />
                    )
                })}
            </div>
        )
    };
};

QuickTour.propTypes = {
    header: PropTypes.string.isRequired,
    tourSections: PropTypes.array.isRequired,
    containerStyle: PropTypes.object,
}

export default QuickTour;
