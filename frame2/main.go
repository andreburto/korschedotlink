// Command gorsche is a desktop slideshow that cycles through the images
// published at https://korsche.link/frame/.
package main

import (
	"fmt"
	"math/rand"
	"net/http"
	"os"
	"time"

	. "modernc.org/tk9.0"
)

const (
	appTitle        = "Gorsche"
	buttonBarHeight = 50
	tickInterval    = 100 * time.Millisecond
	httpTimeout     = 15 * time.Second
)

// gorsche holds the mutable state of the running application. It is only
// ever touched from the Tk main (GUI) goroutine; background goroutines
// communicate results back via PostEvent.
type gorsche struct {
	client   *http.Client
	settings *Settings
	entries  []string
	cache    map[int][]byte

	display *LabelWidget
	prevBtn *TButtonWidget
	rndBtn  *TButtonWidget
	nextBtn *TButtonWidget
	dialog  *ToplevelWidget

	index   int
	photo   *Img
	loading bool
	elapsed time.Duration
}

func main() {
	Initialize()

	settings, err := loadSettings()
	if err != nil {
		fatal("Could not load settings: %v", err)
	}

	client := &http.Client{Timeout: httpTimeout}

	entries, err := fetchIndex(client)
	if err != nil {
		fatal("Could not download the image list: %v", err)
	}

	g := &gorsche{
		client:   client,
		settings: settings,
		entries:  entries,
		cache:    make(map[int][]byte),
		index:    rand.Intn(len(entries)),
	}

	g.buildUI()
	g.loadCurrent()
	g.startAutoCycle()

	App.WmTitle(appTitle)
	WmGeometry(App, fmt.Sprintf("%dx%d", g.settings.AppWidth, g.settings.AppHeight))
	App.SetResizable(false, false)
	App.Center().Wait()
}

// fatal reports a startup error via a message box and exits. It is only used
// before the main window has been built.
func fatal(format string, args ...any) {
	Initialize()
	MessageBox(Icon("error"), Msg(fmt.Sprintf(format, args...)), Title(appTitle))
	os.Exit(1)
}

// buildUI lays out the display area and the <<< / RND / >>> button bar, per
// the design in frame.md.
func (g *gorsche) buildUI() {
	displayW := g.settings.AppWidth
	displayH := g.settings.AppHeight - buttonBarHeight
	if displayH < 1 {
		displayH = 1
	}

	g.display = Label(Width(displayW), Height(displayH), Background(Black), Anchor("center"))
	g.prevBtn = TButton(Txt("<<<"), Command(func() { g.navigate(-1) }))
	g.rndBtn = TButton(Txt("RND"), Command(g.navigateRandom))
	g.nextBtn = TButton(Txt(">>>"), Command(func() { g.navigate(1) }))

	Bind(g.display, "<Button-1>", Command(g.showImageURL))

	Grid(g.display, Row(0), Column(0), Columnspan(3), Sticky("news"))
	Grid(g.prevBtn, Row(1), Column(0), Sticky("we"), Ipady("2m"))
	Grid(g.rndBtn, Row(1), Column(1), Sticky("we"), Ipady("2m"))
	Grid(g.nextBtn, Row(1), Column(2), Sticky("we"), Ipady("2m"))

	GridRowConfigure(App, 0, Weight(1))
	GridColumnConfigure(App, 0, Weight(1))
	GridColumnConfigure(App, 1, Weight(1))
	GridColumnConfigure(App, 2, Weight(1))
}

// showImageURL displays a dialog containing the URL of the current image,
// with a "Copy to clipboard" button and a "Close" button. The dialog is a
// regular Tk toplevel rather than a blocking MessageBox so the auto-cycle
// ticker keeps running while it is open.
func (g *gorsche) showImageURL() {
	if g.dialog != nil {
		return
	}

	url := imageURL(g.entries[g.index])
	dlg := Toplevel()
	g.dialog = dlg
	dlg.WmTitle(appTitle)
	WmTransient(dlg, App)

	closeDialog := func() {
		GrabRelease(dlg)
		Destroy(dlg)
		g.dialog = nil
	}
	WmProtocol(dlg.Window, "WM_DELETE_WINDOW", closeDialog)

	// Tk's clipboard maps onto the native clipboard on Windows, macOS and X11.
	copyURL := func() {
		ClipboardClear()
		ClipboardAppend(url)
	}

	msg := dlg.Label(Txt(url), Wraplength("8c"), Justify("center"))
	buttons := dlg.Frame()
	copyBtn := buttons.TButton(Txt("Copy to clipboard"), Command(copyURL))
	closeBtn := buttons.TButton(Txt("Close"), Command(closeDialog))
	Pack(msg, Padx("4m"), Pady("4m"))
	Pack(buttons, Pady("2m"))
	Pack(copyBtn, closeBtn, Side("left"), Padx("2m"))

	dlg.Center()
	GrabSet(dlg)
	Focus(closeBtn)
}

// startAutoCycle starts a short-interval ticker that advances to the next
// image once the configured delay has elapsed. Using a short tick with an
// accumulator (rather than one ticker per delay) lets navigation actions
// reset the countdown without needing to cancel/recreate the ticker.
func (g *gorsche) startAutoCycle() {
	delay := time.Duration(g.settings.Delay) * time.Millisecond
	NewTicker(tickInterval, func() {
		if g.loading {
			return
		}
		g.elapsed += tickInterval
		if g.elapsed >= delay {
			g.navigate(1)
		}
	})
}

// navigate moves to the next (delta=1) or previous (delta=-1) image,
// wrapping around at the ends of the list, and resets the auto-cycle delay.
func (g *gorsche) navigate(delta int) {
	if g.loading {
		return
	}
	n := len(g.entries)
	g.index = ((g.index+delta)%n + n) % n
	g.elapsed = 0
	g.loadCurrent()
}

// navigateRandom jumps to a random image and resets the auto-cycle delay.
func (g *gorsche) navigateRandom() {
	if g.loading {
		return
	}
	g.index = rand.Intn(len(g.entries))
	g.elapsed = 0
	g.loadCurrent()
}

// loadCurrent downloads (or reuses a cached copy of) the image at g.index,
// resizes it to fit the display area, and shows it. The network/decoding
// work happens on a background goroutine so the GUI stays responsive; the
// result is delivered back to the main thread via PostEvent.
func (g *gorsche) loadCurrent() {
	g.setLoading(true)
	idx := g.index
	displayW := g.settings.AppWidth
	displayH := g.settings.AppHeight - buttonBarHeight
	if displayH < 1 {
		displayH = 1
	}

	go func() {
		raw, err := g.imageBytes(idx)
		if err != nil {
			PostEvent(func() { g.handleLoadError(idx, err) }, false)
			return
		}

		resized, err := resizeToFit(raw, displayW, displayH)
		if err != nil {
			PostEvent(func() { g.handleLoadError(idx, err) }, false)
			return
		}

		PostEvent(func() { g.applyImage(idx, resized) }, false)
	}()
}

// imageBytes returns the raw bytes for entries[idx], downloading and caching
// them on first use.
func (g *gorsche) imageBytes(idx int) ([]byte, error) {
	if data, ok := g.cache[idx]; ok {
		return data, nil
	}
	data, err := fetchImage(g.client, g.entries[idx])
	if err != nil {
		return nil, err
	}
	g.cache[idx] = data
	return data, nil
}

// applyImage displays a resized image, unless a newer navigation request has
// since superseded it.
func (g *gorsche) applyImage(idx int, data []byte) {
	if idx != g.index {
		g.setLoading(false)
		return
	}

	old := g.photo
	g.photo = NewPhoto(Data(data))
	g.display.Configure(Image(g.photo))
	if old != nil {
		old.Delete()
	}
	g.setLoading(false)
}

func (g *gorsche) handleLoadError(idx int, err error) {
	g.setLoading(false)
	if idx != g.index {
		return
	}
	MessageBox(Icon("error"), Msg(fmt.Sprintf("Could not load image: %v", err)), Title(appTitle))
}

// setLoading disables navigation while a load is in flight, preventing
// overlapping downloads from concurrent clicks or an auto-cycle tick.
func (g *gorsche) setLoading(v bool) {
	g.loading = v
	state := "normal"
	if v {
		state = "disabled"
	}
	g.prevBtn.Configure(State(state))
	g.rndBtn.Configure(State(state))
	g.nextBtn.Configure(State(state))
}
