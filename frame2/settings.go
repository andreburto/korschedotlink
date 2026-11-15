package main

import (
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
)

const settingsFileName = "settings.json"

const (
	defaultDelay     = 30000
	defaultAppWidth  = 800
	defaultAppHeight = 600
)

// Settings holds the user-configurable values persisted in settings.json,
// which lives next to the Gorsche executable.
type Settings struct {
	Delay     int `json:"delay"`
	AppWidth  int `json:"app_width"`
	AppHeight int `json:"app_height"`
}

func defaultSettings() *Settings {
	return &Settings{
		Delay:     defaultDelay,
		AppWidth:  defaultAppWidth,
		AppHeight: defaultAppHeight,
	}
}

// settingsPath returns the location of settings.json, kept alongside the
// running executable so the file travels with the app.
func settingsPath() (string, error) {
	exe, err := os.Executable()
	if err != nil {
		return "", err
	}
	return filepath.Join(filepath.Dir(exe), settingsFileName), nil
}

// loadSettings reads settings.json, creating it with default values if it
// does not exist yet. Missing or invalid individual fields fall back to
// their defaults.
func loadSettings() (*Settings, error) {
	path, err := settingsPath()
	if err != nil {
		return nil, err
	}

	data, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		s := defaultSettings()
		if err := saveSettings(path, s); err != nil {
			return nil, err
		}
		return s, nil
	}
	if err != nil {
		return nil, err
	}

	s := defaultSettings()
	if err := json.Unmarshal(data, s); err != nil {
		return nil, err
	}
	if s.Delay <= 0 {
		s.Delay = defaultDelay
	}
	if s.AppWidth <= 0 {
		s.AppWidth = defaultAppWidth
	}
	if s.AppHeight <= 0 {
		s.AppHeight = defaultAppHeight
	}
	return s, nil
}

func saveSettings(path string, s *Settings) error {
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}
