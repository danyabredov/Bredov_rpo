package com.example.backend.controllers;

import com.example.backend.models.Painting;
import com.example.backend.repositories.PaintingRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@CrossOrigin(origins = "http://localhost:3000")
@RestController
@RequestMapping("/api/v1")
public class PaintingController {
    @Autowired
    PaintingRepository paintingRepository;

    @GetMapping("/paintings")
    public List<Painting> getAllPaintings() {
        return paintingRepository.findAll();
    }

    @PostMapping("/paintings")
    public ResponseEntity<?> createPainting(@Validated @RequestBody Painting paint) {
        try {
            Painting nm = paintingRepository.save(paint);
            return new ResponseEntity(nm, HttpStatus.OK);
        }
        catch (Exception ex) {
            String error;
            if (ex.getMessage().contains("paintings.name_UNIQUE"))
                error = "painting_already_exists";
            else
                error = "undefined_error";
            Map<String, String> map = new HashMap<>();
            map.put("error", error);
            return new ResponseEntity<Object>(map, HttpStatus.OK);
        }
    }

    @PutMapping("/paintings/{id}")
    public ResponseEntity<Painting> updatePainting(@PathVariable(value = "id") Long paintId,
                                                   @Validated @RequestBody Painting paintingDetalis) {
        Painting paint = null;
        Optional<Painting> cc = paintingRepository.findById(paintId);
        if (cc.isPresent()) {
            paint = cc.get();
            paint.name = paintingDetalis.name;
            paintingRepository.save(paint);
        } else
            throw new ResponseStatusException(
                    HttpStatus.NOT_FOUND, "museum not found"
            );
        return ResponseEntity.ok(paint);
    }

    @DeleteMapping("/paintings/{id}")
    public Map<String, Boolean> deletePainting(@PathVariable(value = "id") Long paintId) {
        Optional<Painting> painting = paintingRepository.findById(paintId);
        Map<String, Boolean> response = new HashMap<>();
        if (painting.isPresent()) {
            paintingRepository.delete(painting.get());
            response.put("deleted", Boolean.TRUE);
        }
        else
            response.put("deleted", Boolean.FALSE);
        return response;
    }
}