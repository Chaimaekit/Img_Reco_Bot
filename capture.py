import os
import time
import cv2
import numpy as np
import pyautogui
from skimage.metrics import structural_similarity as ssim
from functools import lru_cache



def capture_oriented_templates():
    orientations = ['left', 'right', 'front', 'back']
    captured = {}
    
    print("\n" + "="*70)
    print("ORIENTATION CAPTURE")
    print("="*70)
    print("\nInstructions:")
    print("  1. Position the object in desired orientation on screen")
    print("  2. Hover mouse over TOP-LEFT corner of the object")
    print("  3. Keep mouse STILL for 2 seconds → auto-capture")
    print("  4. Repeat for all 4 orientations (left/right/front/back)")
    print("  5. Press Ctrl+C when finished\n")
    
    try:
        while True:
            print("\n" + "-"*70)
            orient = input(f"Which orientation to capture? {orientations}: ").strip().lower()
            if orient not in orientations:
                print(f"✗ Invalid orientation. Choose from: {orientations}")
                continue
            
            print(f"\n→ Hover mouse over TOP-LEFT of {orient}-facing object (5 sec countdown)...")
            time.sleep(5)
            
            positions = []
            stable_start = None
            timeout = 15
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                pos = pyautogui.position()
                positions.append(pos)
                
                if len(positions) >= 20:
                    recent = positions[-20:]
                    dx = max(p.x for p in recent) - min(p.x for p in recent)
                    dy = max(p.y for p in recent) - min(p.y for p in recent)
                    
                    if dx < 3 and dy < 3:
                        if stable_start is None:
                            stable_start = time.time()
                        elif time.time() - stable_start > 2.0:
                            stable_pos = (recent[0].x, recent[0].y)
                            print(f"\n✓ Mouse stable at {stable_pos} - capturing {orient} template...")
                            
                            region_size = (80, 100)
                            left = stable_pos[0] - 5
                            top = stable_pos[1] - 5
                            
                            screenshot = pyautogui.screenshot(
                                region=(left, top, region_size[0], region_size[1])
                            )
                            filename = f'Object_{orient}.png'
                            screenshot.save(filename)
                            captured[orient] = filename
                            print(f"✓ Saved: {filename}")
                            break
                    else:
                        stable_start = None
                
                time.sleep(0.1)
            else:
                print(f"✗ Timeout: Mouse not stable enough for {orient} capture")
    
    except KeyboardInterrupt:
        print("\n\nCapture session ended.")
        if captured:
            print(f"✓ Successfully captured {len(captured)}/{len(orientations)} orientations:")
            for orient, path in captured.items():
                print(f"   - {orient}: {path}")
        else:
            print("⚠ No templates captured!")
        return captured


@lru_cache(maxsize=32)
def load_template_cached(image_path):
    if not os.path.isfile(image_path):
        return None, None
    
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        return None, None
    
    if img.shape[2] == 4:
        alpha = img[:, :, 3]
        mask = (alpha > 30).astype(np.uint8) * 255 
        rgb = img[:, :, :3]
        return rgb, mask
    return img, None

def detect_in_orientation(screen_gray, template_gray, template_mask=None, scales=None):
    if scales is None:
        scales = [0.9, 0.95, 1.0, 1.05, 1.1]
    
    best = {'val': 0, 'loc': None, 'scale': 1.0}
    
    for scale in scales:
        tw = max(5, int(template_gray.shape[1] * scale))
        th = max(5, int(template_gray.shape[0] * scale))
        tmpl_scaled = cv2.resize(template_gray, (tw, th), interpolation=cv2.INTER_AREA)
        
        mask_scaled = None
        if template_mask is not None:
            mask_scaled = cv2.resize(template_mask, (tw, th), interpolation=cv2.INTER_NEAREST)
            mask_scaled = (mask_scaled > 127).astype(np.uint8) * 255
        
        if mask_scaled is not None and mask_scaled.shape == tmpl_scaled.shape:
            res = cv2.matchTemplate(screen_gray, tmpl_scaled, cv2.TM_CCOEFF_NORMED, mask=mask_scaled)
        else:
            res = cv2.matchTemplate(screen_gray, tmpl_scaled, cv2.TM_CCOEFF_NORMED)
        
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val > best['val']:
            best.update({'val': max_val, 'loc': max_loc, 'scale': scale, 'size': (tw, th)})
    
    return best

def detect_multi_orientation(orientations=('left', 'right', 'front', 'back'), template_threshold=0.58, enable_debug=True, search_region=None):
    start = time.time()
    
    try:
        screenshot = pyautogui.screenshot(region=search_region)
        screen_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        return False, f"Screenshot failed: {e}", None, None
    best_overall = {'val': 0, 'loc': None, 'orient': None, 'size': None, 'scale': 1.0}
    
    for orient in orientations:
        template_path = f'Object_{orient}.png'
        if not os.path.isfile(template_path):
            continue
        
        template_bgr, template_mask = load_template_cached(template_path)
        if template_bgr is None:
            continue
        
        template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
        
        result = detect_in_orientation(
            screen_gray, 
            template_gray, 
            template_mask,
            scales=[0.9, 0.95, 1.0, 1.05, 1.1]
        )
        
        if result['val'] > best_overall['val']:
            best_overall.update({
                'val': result['val'],
                'loc': result['loc'],
                'orient': orient,
                'size': result['size'],
                'scale': result['scale']
            })
    
    if best_overall['val'] < template_threshold:
        elapsed = time.time() - start
        orient_list = ', '.join(orientations)
        return False, (f"Best match {best_overall['val']:.3f} < threshold {template_threshold} "
                      f"(tried: {orient_list}, time: {elapsed*1000:.0f}ms)"), None, None
    
    x, y = best_overall['loc']
    w, h = best_overall['size']
    
    if search_region:
        x += search_region[0]
        y += search_region[1]
    
    full_screen = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    if x < 0 or y < 0 or (x + w) > full_screen.shape[1] or (y + h) > full_screen.shape[0]:
        return False, "Match outside screen bounds", None, None
    
    center = (x + w // 2, y + h // 2)
    elapsed = time.time() - start
    
    if enable_debug:
        debug = full_screen.copy()
        cv2.rectangle(debug, (x, y), (x + w, y + h), (0, 255, 0), 2)
        label = f"{best_overall['orient']}:{best_overall['val']:.2f}"
        cv2.putText(debug, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        debug_path = f"debug_match_{int(time.time())}.jpg"
        cv2.imwrite(debug_path, debug)
        print(f"[DEBUG] Saved match visualization → {debug_path}")
    
    details = (f"✓ {best_overall['orient'].upper()} object @ {center} "
              f"(conf={best_overall['val']:.3f}, scale={best_overall['scale']:.2f}, "
              f"{elapsed*1000:.0f}ms)")
    
    return True, details, center, best_overall['orient']


if __name__ == "__main__":
    # print("\n" + "="*70)
    # print("OBJET DETECTION - ALL ORIENTATIONS")
    # print("="*70)
    
    # # Check if templates exist
    # orientations = ['left', 'right', 'front', 'back']
    # missing = [o for o in orientations if not os.path.isfile(f'Object_{o}.png')]
    
    # if missing:
    #     print(f"\n⚠ Missing templates for orientations: {missing}")
    #     print("   Options:")
    #     print("   1. Run capture_oriented_templates() to create them now")
    #     print("   2. Continue with available orientations only")
    #     choice = input("\nCapture missing templates? (y/n): ").strip().lower()
        
    #     if choice == 'y':
    #         capture_oriented_templates()
    #         # Re-check after capture
    #         missing = [o for o in orientations if not os.path.isfile(f'Object{o}.png')]
    #         if missing:
    #             print(f"\n⚠ Still missing: {missing}. Using available orientations only.")
    #             orientations = [o for o in orientations if o not in missing]
    #     else:
    #         orientations = [o for o in orientations if o not in missing]
    #         if not orientations:
    #             print("✗ No templates available. Exiting.")
    #             exit(1)
    orientations = ['left', 'right', 'front', 'back']
    
    print(f"\n✓ Using templates for orientations: {orientations}")
    print("\n→ Switch to desired window (detection starts in 3 seconds)...")
    time.sleep(3)
    
    detected, details, location, orient = detect_multi_orientation(
        orientations=orientations,
        template_threshold=0.58,
        enable_debug=True,
    )
    
    print("\n" + "="*70)
    print(f"RESULT: {'✅ DETECTED' if detected else '❌ NOT FOUND'}")
    print(f"DETAILS: {details}")
    if detected:
        print(f"ORIENTATION: {orient.upper()}")
        print(f"COORDS:      {location}")
    print("="*70 + "\n")
    
    if not detected:
        print("💡 TROUBLESHOOTING:")
        print("   1. Check debug_match_*.jpg – is green box near the object?")
        print("   2. If match value 0.45-0.58: lower threshold to 0.50 temporarily")
        print("   3. Missing an orientation? Capture it with capture_oriented_templates()")
        print("   4. Object partially off-screen? Maximize desired window")