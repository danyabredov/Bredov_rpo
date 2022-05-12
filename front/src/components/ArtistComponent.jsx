import React, {useEffect, useState} from 'react';
import BackendService from '../services/BackendService';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome';
import {faChevronLeft, faSave} from '@fortawesome/fontawesome-free-solid';
import {alertActions} from "../utils/Rdx";
import {connect} from "react-redux";
import {Form} from "react-bootstrap";
import {useNavigate, useParams} from "react-router-dom";
 
const ArtistComponent = props => {
    const params = useParams();
    const [id, setId] = useState(params.id);
    const [name, setName] = useState("");
    const [countryid, setCountryid] = useState("");
    const [age, setAge] = useState("");
    const [hidden, setHidden] = useState(false);
    const navigate = useNavigate();
 
    useEffect(() => {
        if (parseInt(id) !== -1) {
            BackendService.retrieveArtist(id)
                .then((resp) => {
                    setName(resp.data.name)
                })
                .catch(() => setHidden(true))
        }
    }, []); // [] нужны для вызова useEffect только один раз при инициализации компонента
    // это нужно для того, чтобы в состояние name каждый раз не записывалось значение из БД
 
    const onSubmit = (event) => {
        event.preventDefault();
        event.stopPropagation();
        let err = null;
        if (!name) err = "Название Artist должно быть указано";
        if (err) props.dispatch(alertActions.error(err));
        let artist = {id, name, countryid, age};
 
        if (parseInt(artist.id) === -1) {
            BackendService.createArtist(artist)
                .then(() => navigate(`/artists`))
                .catch(() => {
                })
        } else {
            BackendService.updateArtist(artist)
                .then(() => navigate(`/artists`))
                .catch(() => {
                })
        }
    }
 
    if (hidden)
        return null;
    return (
        <div className="m-4">
            <div className=" row my-2 mr-0">
                <h3>Страна</h3>
                <button className="btn btn-outline-secondary ml-auto"
                        onClick={() => navigate(`/artists`)}
                ><FontAwesomeIcon icon={faChevronLeft}/>{' '}Назад</button>
            </div>
            <Form onSubmit={onSubmit}>
                <Form.Group>
                    <Form.Label>Имя</Form.Label>
                    <Form.Control
                           type="text"
                           placeholder="Введите имя artist"
                           onChange={(e) => {setName(e.target.value)}}
                           value={name}
                           name="name"
                           autoComplete="off"
                    />
                </Form.Group>
                <Form.Group>
                    <Form.Label>Страна</Form.Label>
                    <Form.Control
                           type="text"
                           placeholder="Введите страну artist"
                           onChange={(e) => {setCountryid(e.target.value)}}
                           value={countryid}
                           name="countryid"
                           autoComplete="off"
                    />
                </Form.Group>
                <Form.Group>
                    <Form.Label>Век</Form.Label>
                    <Form.Control
                           type="text"
                           placeholder="Введите век artist"
                           onChange={(e) => {setAge(e.target.value)}}
                           value={age}
                           name="age"
                           autoComplete="off"
                    />
                </Form.Group>
                <button className="btn btn-outline-secondary" type="submit">
                    <FontAwesomeIcon icon={faSave}/>{' '}
                    Сохранить
                </button>
            </Form>
        </div>
    )
}
 
export default connect()(ArtistComponent);