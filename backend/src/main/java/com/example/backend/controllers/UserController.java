package com.example.backend.controllers;

import com.example.backend.models.Artist;
import com.example.backend.models.Museum;
import com.example.backend.models.User;
import com.example.backend.tools.DataValidationException;
import com.example.backend.tools.Utils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.codec.Hex;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import com.example.backend.repositories.MuseumRepository;
import com.example.backend.repositories.UserRepository;
import org.springframework.web.server.ResponseStatusException;

import javax.validation.Valid;
import java.util.*;

@CrossOrigin(origins = "http://localhost:3000")
@RestController
@RequestMapping("/api/v1")
public class UserController {
    @Autowired
    UserRepository userRepository;
    @Autowired
    MuseumRepository museumRepository;
/*    @GetMapping("/users")
    public List
    getAllUsers() {
        return userRepository.findAll();
    } */

    @GetMapping("/users")
    public Page getAllUsers(@RequestParam("page") int page, @RequestParam("limit") int limit) {
        return userRepository.findAll(PageRequest.of(page, limit, Sort.by(Sort.Direction.ASC, "name")));
    }

    @GetMapping("/users/{id}")
    public ResponseEntity getUser(@PathVariable(value = "id") Long userId)
            throws DataValidationException
    {
        User user = userRepository.findById(userId)
                .orElseThrow(()-> new DataValidationException("user с таким индексом не найден"));
        return ResponseEntity.ok(user);
    }

    @PostMapping("/deleteusers")
    public ResponseEntity deleteUsers(@Valid @RequestBody List users) {
        userRepository.deleteAll(users);
        return new ResponseEntity(HttpStatus.OK);
    }

/*    @PostMapping("/users")
    public ResponseEntity<Object> createUser(@RequestBody User user)
            throws Exception {
        try {
            User nc = userRepository.save(user);
            return new ResponseEntity<Object>(nc, HttpStatus.OK);
        }
        catch(Exception ex) {
            String error;
            if (ex.getMessage().contains("users.name_UNIQUE"))
                error = "useralreadyexists";
            else
                error = "undefinederror";
            Map<String, String>
                    map = new HashMap<>();
            map.put("error", error);
            return ResponseEntity.ok(map);
        }
    }
*/
    @PostMapping("/users/{id}/addmuseums")
    public ResponseEntity<Object> addMuseums(@PathVariable(value = "id") Long userId,
                                             @Validated @RequestBody Set<Museum> museums) {
        Optional<User> uu = userRepository.findById(userId);
        int cnt = 0;
        if (uu.isPresent()) {
            User u = uu.get();
            for (Museum m: museums) {
                Optional<Museum> mm = museumRepository.findById(m.id);
                if(mm.isPresent()) {
                    u.addMuseum(mm.get());
                    cnt++;
                }
            }
            userRepository.save(u);
        }
        Map<String, String> responce = new HashMap<>();
        responce.put("count", String.valueOf(cnt));
        return ResponseEntity.ok(responce);
    }

    @PostMapping("/users/{id}/removemuseums")
    public ResponseEntity<Object> removeMuseums(@PathVariable(value = "id") Long userId,
                                                @Validated @RequestBody Set<Museum> museums) {
        Optional<User> uu = userRepository.findById(userId);
        int cnt = 0;
        if (uu.isPresent()) {
            User u = uu.get();
            for (Museum m: museums) {
                u.addMuseum(m);
                cnt++;
            }
            userRepository.save(u);
        }
        Map<String, String> responce = new HashMap<>();
        responce.put("count", String.valueOf(cnt));
        return ResponseEntity.ok(responce);
    }

/*    @GetMapping("/countries/{id}/artists")
    public ResponseEntity<List<Artist>> getCountryArtists(@PathVariable(value = "id") Long countryId) {
        Optional<Country> cc = countryRepository.findById(countryId);
        return cc.map(country -> ResponseEntity.ok(country.artists)).orElseGet(() -> ResponseEntity.ok(new ArrayList<>()));
    }
*/
    @PutMapping("/users/{id}")
    public ResponseEntity<User> updateUser(@PathVariable(value = "id") Long userId,
                                           @Valid @RequestBody User userDetails) throws DataValidationException {
        try {
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new DataValidationException("Пользователь с таким индексом не найден"));
            user.email = userDetails.email;
            String np = userDetails.np;
            if (np != null && !np.isEmpty()) {
                byte[] b = new byte[32];
                new Random().nextBytes(b);
                String sait = new String(Hex.encode(b));
                user.password = Utils.ComputeHash(np, sait);
                user.sait = sait;
            }
            userRepository.save(user);
            return ResponseEntity.ok(user);
        }
        catch (Exception ex) {
            String error;
            if (ex.getMessage().contains("users.email_UNIQUE"))
                throw new DataValidationException("Пользователь с такой почтой уже есть в базе");
            else
                throw new DataValidationException("Неизвестная ошибка");
        }
    }
/*
    @DeleteMapping("/users/{id}")
    public Map<String, Boolean> deleteUser(@PathVariable(value = "id") Long userId) {
        Optional<User> user = userRepository.findById(userId);
        Map<String, Boolean> response = new HashMap<>();
        if (user.isPresent()) {
            userRepository.delete(user.get());
            response.put("deleted", Boolean.TRUE);
        }
        else
            response.put("deleted", Boolean.FALSE);
        return response;
    } */
}
