from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExerciseInstructionSeed:
    overview: str
    setup_steps: tuple[str, ...]
    execution_steps: tuple[str, ...]
    form_cues: tuple[str, ...]
    common_mistakes: tuple[str, ...]
    safety_notes: tuple[str, ...]


@dataclass(frozen=True)
class _SeedDefinition:
    name: str
    template_key: str
    distinctive_step: str


def _template(
    overview: str,
    setup: tuple[str, ...],
    execution: tuple[str, ...],
    cues: tuple[str, ...],
    mistakes: tuple[str, ...],
    safety: tuple[str, ...],
) -> ExerciseInstructionSeed:
    return ExerciseInstructionSeed(overview, setup, execution, cues, mistakes, safety)


_TEMPLATES = {
    "push_up": _template(
        "is a bodyweight press that trains the chest, shoulders, and triceps while the trunk stays braced.",
        (
            "Place the hands on the support at about shoulder width.",
            "Set the feet back and make a straight line from head to heels.",
        ),
        (
            "Bend the elbows and lower the chest under control.",
            "Press the support away until the elbows are straight without losing body position.",
        ),
        (
            "Keep the ribs and hips moving together.",
            "Aim the elbows diagonally back rather than straight out.",
        ),
        (
            "Letting the hips sag or pike.",
            "Shortening the range by reaching the head forward.",
        ),
        ("Use a hand height and range that let the shoulders move comfortably.",),
    ),
    "pike_press": _template(
        "is a bodyweight overhead-press variation that places extra demand on the shoulders and triceps.",
        (
            "Start on hands and feet with the hips lifted high.",
            "Place the hands slightly wider than the shoulders and look toward the floor.",
        ),
        (
            "Bend the elbows and lower the crown of the head toward the space between the hands.",
            "Press the floor away and return to the high-hip position.",
        ),
        (
            "Keep the hips high throughout the repetition.",
            "Let the elbows travel diagonally back.",
        ),
        (
            "Turning the movement into a flat push-up.",
            "Dropping quickly onto the hands.",
        ),
        (
            "Reduce the range or elevate the hands if the shoulders cannot stay comfortable.",
        ),
    ),
    "dip": _template(
        "is a bodyweight triceps press performed from a stable bench.",
        (
            "Sit at the bench edge and place the hands beside the hips.",
            "Move the hips just off the bench with the feet planted securely.",
        ),
        (
            "Bend the elbows and lower only as far as the shoulders remain comfortable.",
            "Press through the palms to straighten the elbows.",
        ),
        (
            "Keep the shoulders down away from the ears.",
            "Keep the hips close to the bench edge.",
        ),
        (
            "Drifting too far away from the bench.",
            "Lowering beyond a comfortable shoulder range.",
        ),
        (
            "Choose another triceps exercise if the bench position irritates the shoulders or wrists.",
        ),
    ),
    "db_press": _template(
        "is a dumbbell chest press that allows each arm to work independently.",
        (
            "Set the bench firmly and plant both feet.",
            "Hold the dumbbells over the chest with the wrists stacked over the elbows.",
        ),
        (
            "Lower the dumbbells with control until the upper arms reach a comfortable depth.",
            "Press the dumbbells up while keeping the shoulders supported by the bench.",
        ),
        (
            "Keep the shoulder blades gently set against the bench.",
            "Keep the wrists straight and forearms nearly vertical.",
        ),
        (
            "Bouncing out of the bottom position.",
            "Letting the dumbbells drift toward the face or stomach.",
        ),
        ("Use a load you can guide safely into and out of position.",),
    ),
    "floor_press": _template(
        "is a floor-based press that limits shoulder extension and emphasizes a controlled lockout.",
        (
            "Lie on the floor with the knees bent and feet planted.",
            "Set the weight above the chest with the wrists stacked over the elbows.",
        ),
        (
            "Lower until the upper arms make gentle contact with the floor.",
            "Pause without relaxing, then press to straight arms.",
        ),
        (
            "Keep the ribs down and shoulders anchored.",
            "Touch the upper arms softly rather than crashing into the floor.",
        ),
        (
            "Using the floor to bounce the elbows.",
            "Losing wrist position as the weight lowers.",
        ),
        (
            "Clear enough floor space to set down the weight without trapping the hands.",
        ),
    ),
    "barbell_press": _template(
        "is a barbell chest press that develops coordinated pressing strength.",
        (
            "Set the bench and rack so the bar can be unracked without reaching.",
            "Plant the feet and take an even grip with the wrists over the forearms.",
        ),
        (
            "Unrack the bar and lower it under control toward the chest.",
            "Press the bar back over the shoulders while maintaining the same body position.",
        ),
        (
            "Keep the shoulder blades supported on the bench.",
            "Keep both sides of the bar level.",
        ),
        (
            "Flaring the elbows straight sideways.",
            "Changing the touch point from repetition to repetition.",
        ),
        ("Use rack safeties or a spotter when the load could pin you.",),
    ),
    "cable_press": _template(
        "is a resisted chest press that keeps steady tension on the chest and triceps through the range.",
        (
            "Set the handles at chest height and brace before pressing.",
            "Start with the hands near the chest and the shoulders down.",
        ),
        (
            "Press the handles forward until the arms are straight.",
            "Return slowly until the chest is comfortably stretched.",
        ),
        (
            "Keep the torso still as the hands move.",
            "Finish with the hands in line with the chest.",
        ),
        (
            "Leaning or twisting to move the resistance.",
            "Letting the shoulders roll forward at the start.",
        ),
        ("Check that the handles and resistance setting are secure before starting.",),
    ),
    "chest_fly": _template(
        "is a chest fly that trains the chest through a wide arm arc with relatively fixed elbows.",
        (
            "Begin with the hands in front of the chest and the elbows softly bent.",
            "Brace the torso before opening the arms.",
        ),
        (
            "Open the arms in a controlled arc until a comfortable chest stretch is reached.",
            "Bring the arms back together without turning the movement into a press.",
        ),
        (
            "Keep the elbow bend nearly constant.",
            "Move from the shoulders while the ribs stay down.",
        ),
        (
            "Using a load that forces excessive depth.",
            "Bending and straightening the elbows to move the weight.",
        ),
        ("Stop the lowering phase before the shoulders feel pinched or unstable.",),
    ),
    "shoulder_press": _template(
        "is an overhead press that trains the shoulders and triceps with a stable trunk.",
        (
            "Set the weight at shoulder height and brace the trunk before pressing.",
            "Brace the trunk with the wrists stacked above the elbows.",
        ),
        (
            "Press overhead until the arms are straight without leaning back.",
            "Lower the weight to shoulder height under control.",
        ),
        (
            "Keep the ribs over the pelvis.",
            "Finish with the arms beside the ears if comfortable.",
        ),
        ("Overarching the lower back.", "Pressing one side faster than the other."),
        (
            "Use a range that does not cause shoulder pinching and keep the area overhead clear.",
        ),
    ),
    "push_press": _template(
        "is a leg-assisted overhead press that transfers controlled lower-body drive into the bar.",
        (
            "Hold the bar at the shoulders with the feet about hip width.",
            "Brace before making a short, balanced dip through the knees.",
        ),
        (
            "Drive through the floor and transfer that force into the press.",
            "Finish overhead, then lower the bar under control to the shoulders.",
        ),
        (
            "Dip straight down with the heels planted.",
            "Keep the bar close as it passes the face.",
        ),
        (
            "Turning the dip into a forward squat.",
            "Pressing before the legs finish driving.",
        ),
        (
            "Use a clear overhead area and a load that can be returned to the shoulders safely.",
        ),
    ),
    "raise": _template(
        "trains the deltoids through a controlled arm path.",
        (
            "Stand tall with the resistance resting by the sides or thighs.",
            "Soften the elbows and brace the trunk.",
        ),
        (
            "Raise the resistance smoothly without swinging.",
            "Pause briefly, then lower to the start under control.",
        ),
        (
            "Lead with the elbows rather than the hands.",
            "Keep the shoulders down away from the ears.",
        ),
        (
            "Using momentum from the hips or back.",
            "Raising beyond a comfortable shoulder range.",
        ),
        ("Choose light resistance that permits smooth shoulder motion.",),
    ),
    "upright_row": _template(
        "is an upright pulling variation for the shoulders and upper traps.",
        (
            "Hold the resistance in front of the thighs with a comfortable grip.",
            "Stand tall and brace the trunk.",
        ),
        (
            "Pull the elbows up and out while keeping the resistance close.",
            "Stop at a comfortable height and lower slowly.",
        ),
        (
            "Let the elbows guide the motion.",
            "Keep the shoulders away from the ears until the pull begins.",
        ),
        (
            "Pulling higher than the shoulders comfortably allow.",
            "Swinging the torso to start the repetition.",
        ),
        (
            "Use a lower stopping point or another raise variation if the shoulders feel pinched.",
        ),
    ),
    "rear_delt": _template(
        "is a rear-shoulder and upper-back raise performed with the arms moving away from the torso.",
        (
            "Brace the torso before the arms move.",
            "Start with the arms hanging and elbows softly bent.",
        ),
        (
            "Open the arms until they are roughly in line with the torso.",
            "Lower slowly without losing the body position.",
        ),
        (
            "Move the upper arms rather than shrugging the shoulders.",
            "Keep the neck relaxed.",
        ),
        (
            "Using torso momentum.",
            "Turning the movement into a row by bending the elbows deeply.",
        ),
        (
            "Use light resistance and stop before the front of the shoulder feels strained.",
        ),
    ),
    "face_pull": _template(
        "is an upper-back and rear-shoulder pull toward the face.",
        (
            "Set the resistance anchor around upper-chest to face height.",
            "Take tension with the arms straight and a stable stance.",
        ),
        (
            "Pull toward the face while separating the hands.",
            "Return until the arms are straight without letting the shoulders roll forward.",
        ),
        (
            "Finish with the elbows high and hands beside the face.",
            "Keep the ribs down and neck long.",
        ),
        (
            "Pulling to the chest instead of the face.",
            "Leaning back to move the resistance.",
        ),
        (
            "Confirm the anchor and attachment are secure before pulling toward the face.",
        ),
    ),
    "db_row": _template(
        "trains the back and elbow flexors while the dumbbells move beside the ribs.",
        (
            "Set the torso firmly before letting the dumbbells hang below the shoulders.",
            "Let the dumbbell hang below the shoulder before starting.",
        ),
        (
            "Pull the elbow toward the hip while keeping the torso steady.",
            "Lower until the arm is straight and the shoulder blade can move naturally.",
        ),
        (
            "Keep the shoulder away from the ear.",
            "Finish by moving the elbow, not twisting the torso.",
        ),
        ("Jerking the weight from the floor.", "Shortening the lowering phase."),
        (
            "Stop the set if torso position cannot be maintained without jerking the weight.",
        ),
    ),
    "barbell_row": _template(
        "trains the back while the hips hold a stable hinge.",
        (
            "Grip the bar evenly and hinge until it hangs below the shoulders.",
            "Brace the trunk and keep the weight balanced over the feet.",
        ),
        (
            "Pull the bar toward the lower ribs or upper waist.",
            "Lower to straight arms without changing the hinge angle.",
        ),
        (
            "Keep the bar close to the legs.",
            "Hold the torso angle steady through the set.",
        ),
        ("Standing up as the bar is pulled.", "Rounding the back to reach lower."),
        (
            "Use a load that lets the hinge stay controlled; set the bar down if the back position changes.",
        ),
    ),
    "supported_row": _template(
        "is a supported horizontal row that trains the back and biceps with reduced demand on the lower back.",
        (
            "Begin with the arms straight and the row station or anchor secure.",
            "Brace the torso before pulling the elbows back.",
        ),
        (
            "Pull the elbows back until the hands approach the torso.",
            "Return slowly until the shoulder blades can reach forward.",
        ),
        (
            "Keep the torso fixed while the elbows move.",
            "Drive the elbows back without shrugging.",
        ),
        (
            "Rocking the body to finish the pull.",
            "Stopping before the arms fully lengthen.",
        ),
        ("Make sure the row station or anchor cannot shift during the set.",),
    ),
    "cable_row": _template(
        "provides continuous resistance for the back and biceps.",
        (
            "Take control of the cable handle with the arms straight and torso braced.",
            "Begin with straight arms and the shoulders relaxed forward.",
        ),
        (
            "Pull the handle toward the torso without changing body position.",
            "Return with control until the arms are straight.",
        ),
        (
            "Keep the torso quiet and the cable path smooth.",
            "Finish with the elbows behind the body without shrugging.",
        ),
        (
            "Leaning far back to complete the pull.",
            "Letting the weight stack slam between repetitions.",
        ),
        ("Check the pin, cable, and attachment before loading the movement.",),
    ),
    "pull_up": _template(
        "is a vertical bodyweight pull for the back, biceps, and grip.",
        (
            "Take a secure grip on the pull-up bar and settle the body before pulling.",
            "Start from a controlled hang with the ribs gently braced.",
        ),
        (
            "Pull the elbows down until the chest approaches the bar or the chin clears it.",
            "Lower under control until the arms are straight.",
        ),
        (
            "Keep the legs and trunk quiet.",
            "Think about driving the elbows toward the ribs.",
        ),
        ("Kicking to create momentum.", "Dropping through the bottom position."),
        (
            "Use assistance or a reduced range if a controlled repetition is not available.",
        ),
    ),
    "pulldown": _template(
        "is an anchored vertical pull that trains the lats and biceps.",
        (
            "Take the overhead resistance with the arms long and the torso braced.",
            "Begin with the arms long and shoulders below the ears.",
        ),
        (
            "Pull the elbows down toward the ribs.",
            "Return slowly until the arms are straight overhead.",
        ),
        (
            "Keep the chest tall without leaning far back.",
            "Pull with the elbows rather than the hands.",
        ),
        ("Turning the movement into a backward lean.", "Pulling behind the neck."),
        ("Confirm the anchor, attachment, and any seat setting are secure.",),
    ),
    "straight_arm_pull": _template(
        "is a straight-arm pulldown pattern that trains the lats without a large elbow bend.",
        (
            "Set the resistance above head height and step back into tension.",
            "Hinge slightly with the arms long and ribs braced.",
        ),
        (
            "Sweep the hands down toward the thighs.",
            "Return overhead slowly while keeping the torso still.",
        ),
        (
            "Keep a soft but fixed elbow bend.",
            "Finish by bringing the upper arms beside the torso.",
        ),
        (
            "Turning the movement into a triceps pressdown.",
            "Arching the back to reach the bottom.",
        ),
        ("Use a secure anchor and enough clearance for the full arm path.",),
    ),
    "squat_body": _template(
        "is a squat pattern that trains the legs while using body position for resistance.",
        (
            "Stand with the feet at a comfortable squat width.",
            "Brace lightly and keep the whole foot in contact with the floor.",
        ),
        (
            "Sit down between the hips and knees to a controlled depth.",
            "Push through the floor to stand tall.",
        ),
        (
            "Track the knees in the same direction as the toes.",
            "Keep pressure across the heel and forefoot.",
        ),
        (
            "Letting the knees collapse inward.",
            "Losing balance onto the toes or heels.",
        ),
        ("Use a depth that remains balanced and comfortable for the knees and hips.",),
    ),
    "squat_db": _template(
        "is a dumbbell squat that adds external load to the legs and trunk.",
        (
            "Secure the dumbbell load close to the body's center before descending.",
            "Set the feet at a comfortable width and brace before descending.",
        ),
        (
            "Lower between the hips and knees while keeping the load controlled.",
            "Drive through the whole foot to return to standing.",
        ),
        ("Keep the load close to the body's center.", "Track the knees over the toes."),
        (
            "Letting the load pull the chest down.",
            "Rushing or bouncing out of the bottom.",
        ),
        ("Choose a load that can be picked up and set down with a stable hinge.",),
    ),
    "squat_barbell": _template(
        "builds leg and trunk strength while the bar stays balanced over the feet.",
        (
            "Set the rack hooks and safeties, then unrack the bar with both feet beneath it.",
            "Step clear and establish a balanced squat stance before descending.",
        ),
        (
            "Brace, then lower through the hips and knees to a controlled depth.",
            "Drive through the floor and stand without letting the bar tip.",
        ),
        (
            "Keep the bar balanced over the middle of the feet.",
            "Track the knees in line with the toes.",
        ),
        (
            "Starting before the stance is settled.",
            "Letting the hips or chest rise much faster than the other.",
        ),
        (
            "Use rack safeties and a load that can be controlled through a stable, comfortable depth.",
        ),
    ),
    "squat_supported": _template(
        "is a supported squat variation that trains the quadriceps and glutes along a guided path.",
        (
            "Adjust the support to fit the body securely.",
            "Place the feet where the knees can track comfortably over the toes.",
        ),
        (
            "Lower through the knees and hips without losing contact with the support.",
            "Press through the feet to return to the start.",
        ),
        (
            "Keep both feet evenly loaded.",
            "Use a smooth depth that you can reverse without bouncing.",
        ),
        (
            "Setting the feet too close to the support.",
            "Locking the knees forcefully at the top.",
        ),
        ("Check that the support is stable before loading it.",),
    ),
    "lunge_body": _template(
        "is a bodyweight single-leg pattern that trains the quadriceps, glutes, and balance.",
        (
            "Stand tall with enough clear floor space for the step.",
            "Set the feet about hip width rather than on one narrow line.",
        ),
        (
            "Move into the exercise's stance and lower the working leg under control.",
            "Push through the working foot to move into the next position.",
        ),
        (
            "Keep the front foot fully planted.",
            "Let the front knee track with the toes.",
        ),
        (
            "Stepping onto a tightrope-width stance.",
            "Pushing mostly from the back foot.",
        ),
        ("Use a shorter range or light hand support if balance is not steady.",),
    ),
    "lunge_loaded": _template(
        "is a loaded single-leg pattern that trains the legs while the trunk controls the resistance.",
        (
            "Secure the external load before establishing the working stance.",
            "Stand with enough clear space and set the feet at hip width.",
        ),
        (
            "Lower through the working leg while keeping the load balanced.",
            "Drive through the working foot to return or advance.",
        ),
        (
            "Keep the load quiet over the base of support.",
            "Maintain full-foot pressure on the working leg.",
        ),
        (
            "Letting the load pull the torso sideways.",
            "Using a step length that forces the heel to lift.",
        ),
        (
            "Choose a load and setup that do not compromise balance before the first step.",
        ),
    ),
    "hinge_db": _template(
        "is a dumbbell hip hinge that trains the hamstrings and glutes while the spine stays long.",
        (
            "Hold the dumbbells close to the thighs and soften the knees.",
            "Brace the trunk and set the feet firmly.",
        ),
        (
            "Push the hips back as the dumbbells travel close to the legs.",
            "Stand by driving the hips forward without leaning back.",
        ),
        (
            "Keep the weight over the midfoot.",
            "Stop the lowering phase when the hamstrings limit the hinge.",
        ),
        ("Squatting the weight straight down.", "Reaching lower by rounding the back."),
        ("Use a range and load that allow the spine to stay controlled.",),
    ),
    "hinge_barbell": _template(
        "is a barbell hip hinge that trains the posterior chain with the bar kept close to the body.",
        (
            "Take an even grip and keep the bar close to the body before moving.",
            "Set the feet, soften the knees, and brace before moving.",
        ),
        (
            "Push the hips back while the bar travels close to the legs.",
            "Drive through the feet and extend the hips to stand tall.",
        ),
        (
            "Keep the lats engaged so the bar does not drift forward.",
            "Maintain a long spine and balanced foot pressure.",
        ),
        ("Pulling the bar away from the legs.", "Finishing by leaning backward."),
        ("Stop the set if the back position cannot be maintained under the load.",),
    ),
    "deadlift": _template(
        "is a floor-start barbell pull that trains the hips, legs, back, and grip together.",
        (
            "Stand with the bar over the middle of the feet and take an even grip.",
            "Bring the shins toward the bar, brace, and take slack out before lifting.",
        ),
        (
            "Push the floor away while the bar rises close to the legs.",
            "Stand tall, then return the bar by hinging before bending the knees.",
        ),
        (
            "Keep the bar close and both feet planted.",
            "Let the hips and shoulders rise together from the floor.",
        ),
        (
            "Jerking the bar before the body is braced.",
            "Letting the bar swing around the knees.",
        ),
        (
            "Use clear floor space and stop if the start position cannot be held safely.",
        ),
    ),
    "bridge": _template(
        "is a hip-extension exercise that emphasizes the glutes and hamstrings.",
        (
            "Set the upper back and feet firmly before lifting the hips.",
            "Brace the trunk and begin with the hips level.",
        ),
        (
            "Drive through the feet and lift the hips until the torso and thighs align.",
            "Lower under control without losing foot position.",
        ),
        (
            "Finish with the glutes rather than arching the lower back.",
            "Keep the knees tracking over the feet.",
        ),
        ("Pushing mostly through the toes.", "Overextending the back at the top."),
        ("Pad and stabilize external load placed across the hips.",),
    ),
    "hamstring_curl": _template(
        "is a knee-flexion exercise that trains the hamstrings while the hips remain controlled.",
        (
            "Position the support or resistance so the heels can move through the full path.",
            "Brace the trunk and keep the hips level before moving the heels.",
        ),
        (
            "Curl the heels toward the hips without losing alignment.",
            "Extend the knees slowly back to the start.",
        ),
        ("Keep the hips level.", "Control both the curling and lengthening phases."),
        (
            "Dropping the hips as the knees bend.",
            "Snapping the legs straight on the return.",
        ),
        (
            "Use a smaller range if the hamstrings cramp or the hips cannot stay controlled.",
        ),
    ),
    "curl": _template(
        "is an elbow-flexion exercise for the biceps and forearms.",
        (
            "Take a secure grip with the wrists straight before curling.",
            "Set the upper arms firmly before beginning the curl.",
        ),
        (
            "Curl by bending the elbow without moving the upper arm forward.",
            "Lower until the elbow is straight while keeping tension controlled.",
        ),
        (
            "Keep the wrist aligned with the forearm.",
            "Let the elbow, not the shoulder, drive the movement.",
        ),
        (
            "Swinging the torso to start the curl.",
            "Dropping quickly through the lowering phase.",
        ),
        (
            "Use a load that does not force the wrist or elbow out of a comfortable path.",
        ),
    ),
    "triceps": _template(
        "is an elbow-extension exercise that targets the triceps with the upper arm kept controlled.",
        (
            "Secure the resistance and set the upper arms before extending the elbows.",
            "Start with the elbows bent and the shoulders stable.",
        ),
        (
            "Straighten the elbows through a comfortable range.",
            "Return slowly without letting the resistance pull the arms out of position.",
        ),
        (
            "Keep the elbows on the same path throughout the repetition.",
            "Move at the elbows rather than the shoulders.",
        ),
        (
            "Letting the elbows flare or drift widely.",
            "Using momentum to finish the lockout.",
        ),
        ("Choose a load and range that keep the elbows comfortable.",),
    ),
    "carry": _template(
        "is a loaded carry that trains grip, trunk control, and whole-body posture while walking.",
        (
            "Pick up the load with a stable hinge.",
            "Stand tall with clear walking space ahead.",
        ),
        (
            "Walk with short, controlled steps for the planned distance or time.",
            "Stop, settle the feet, and return the load to the floor with a hinge.",
        ),
        (
            "Keep the ribs stacked over the pelvis.",
            "Keep the load quiet rather than letting it swing.",
        ),
        ("Leaning away from or toward the load.", "Rushing the turns or set-down."),
        ("Use a clear path and a grip you can maintain without dropping the load.",),
    ),
    "plank": _template(
        "is a bracing exercise that trains the trunk to resist unwanted extension or rotation.",
        (
            "Set the upper-body support directly beneath the shoulders.",
            "Extend the legs and create a straight, supported body line.",
        ),
        (
            "Brace before beginning the exercise-specific hold or limb movement.",
            "Finish the interval before the trunk position changes.",
        ),
        (
            "Keep the ribs and pelvis facing the same direction.",
            "Create active pressure into the floor through the upper-body support.",
        ),
        ("Holding the breath unnecessarily.", "Letting the hips sag, pike, or rotate."),
        (
            "Shorten the hold or use an easier support if the lower back cannot stay comfortable.",
        ),
    ),
    "floor_core": _template(
        "is a floor-based core exercise that trains controlled trunk and hip movement.",
        (
            "Use a clear floor area and settle the trunk before moving the limbs.",
            "Brace gently so the ribs stay connected to the pelvis.",
        ),
        (
            "Move the working limbs slowly without losing trunk position.",
            "Return to the start before the lower back loses control.",
        ),
        (
            "Use a slow exhale during the hardest part.",
            "Keep the movement smaller than the available trunk control.",
        ),
        (
            "Using momentum instead of abdominal control.",
            "Forcing a range that lifts or arches the lower back.",
        ),
        ("Reduce the lever length or range if the lower back feels strained.",),
    ),
    "anti_rotation": _template(
        "is an anti-rotation core exercise that challenges the trunk to stay square against side pull.",
        (
            "Set the anchored resistance at about chest height and stand side-on.",
            "Take enough distance to create steady tension.",
        ),
        (
            "Keep the hands controlled while resisting rotation toward the anchor.",
            "Return under control without turning toward the anchor.",
        ),
        (
            "Keep the hips and shoulders facing forward.",
            "Stay tall rather than leaning away from the resistance.",
        ),
        (
            "Rotating to make the resistance easier.",
            "Using a stance too narrow to control.",
        ),
        ("Use a secure anchor and resistance that does not pull you off balance.",),
    ),
    "hanging_core": _template(
        "is a hanging core exercise that combines grip with controlled hip and trunk movement.",
        (
            "Take a secure grip on the pull-up bar and settle into a controlled hang.",
            "Brace before moving the legs.",
        ),
        (
            "Raise the knees or legs using the abdominals rather than a swing.",
            "Lower slowly until the body is quiet again.",
        ),
        (
            "Start each repetition from a still hang.",
            "Keep the shoulders active rather than collapsing into the joints.",
        ),
        ("Kipping the legs for momentum.", "Dropping the legs quickly."),
        ("Use a lower leg height or stop if grip or shoulder control is fading.",),
    ),
    "hang": _template(
        "is a pull-up-bar hold that trains grip and controlled shoulder positioning.",
        (
            "Use a secure bar and a comfortable shoulder-width grip.",
            "Use a step to take body weight gradually without swinging.",
        ),
        (
            "Hold the exercise-specific arm position while breathing normally.",
            "Step down under control before the grip opens.",
        ),
        (
            "Keep the body quiet beneath the bar.",
            "Keep the shoulders controlled throughout the hold.",
        ),
        (
            "Swinging or twisting during the hold.",
            "Staying up after grip control is lost.",
        ),
        ("Use a step for a controlled exit and avoid dropping from the bar.",),
    ),
    "body_conditioning": _template(
        "is a bodyweight conditioning movement that coordinates the trunk and limbs at a sustainable pace.",
        (
            "Clear enough floor space for the full movement.",
            "Establish a stable starting position before increasing the pace.",
        ),
        (
            "Repeat the movement smoothly at the planned effort.",
            "Slow down before posture or foot placement becomes inconsistent.",
        ),
        ("Keep breathing steady.", "Favor quiet, deliberate contacts with the floor."),
        (
            "Starting faster than can be sustained.",
            "Trading control for repetition speed.",
        ),
        ("Stop if sharp pain, dizziness, or loss of balance occurs.",),
    ),
    "treadmill": _template(
        "provides controlled indoor conditioning with deliberate speed and incline changes.",
        (
            "Clip the safety key on and begin at an easy walking speed.",
            "Set the planned incline and speed only after balance is settled.",
        ),
        (
            "Walk or run near the center of the belt with a steady rhythm.",
            "Adjust speed or incline gradually between work and recovery periods.",
        ),
        (
            "Look ahead and let the arms swing naturally.",
            "Keep the stride smooth and reduce speed before form becomes rushed.",
        ),
        (
            "Holding the rails while using a speed that is too high.",
            "Stepping off a moving belt.",
        ),
        ("Reduce the speed before changing position or ending the session.",),
    ),
    "bike": _template(
        "is a stationary-bike conditioning session using controlled cadence and resistance.",
        (
            "Adjust the seat so the knee remains slightly bent at the bottom of the pedal stroke.",
            "Begin with light resistance and settle both feet securely.",
        ),
        (
            "Pedal smoothly at the planned cadence and effort.",
            "Change resistance gradually for work and recovery periods.",
        ),
        (
            "Keep the knees tracking forward.",
            "Relax the hands and shoulders while the legs do the work.",
        ),
        (
            "Bouncing on the seat from excessive cadence.",
            "Using resistance that makes the pedal stroke jerky.",
        ),
        ("Slow the pedals before dismounting and adjust the bike only when stable.",),
    ),
    "calf_foot": _template(
        "trains the lower leg through controlled ankle and foot action.",
        (
            "Stand tall near light support if needed.",
            "Set the feet parallel and distribute weight evenly.",
        ),
        (
            "Move through the exercise's ankle or foot action under control.",
            "Return slowly rather than dropping into the end position.",
        ),
        (
            "Keep the ankles tracking straight ahead.",
            "Use a smooth range from the feet rather than bouncing.",
        ),
        (
            "Rolling onto the outer edges of the feet.",
            "Using momentum instead of ankle motion.",
        ),
        ("Use support and a smaller range if balance is uncertain.",),
    ),
    "shoulder_rotation": _template(
        "is a light shoulder-rotation exercise for controlled rotator-cuff movement.",
        (
            "Set light resistance level with the working elbow.",
            "Take light tension and keep the working upper arm still.",
        ),
        (
            "Rotate the forearm through a comfortable arc while the upper arm stays still.",
            "Return slowly to the start.",
        ),
        (
            "Keep the shoulder down and centered.",
            "Use a small, controlled range rather than forcing motion.",
        ),
        (
            "Moving the whole torso with the arm.",
            "Choosing resistance that changes the elbow position.",
        ),
        ("This is a control drill; stop if the shoulder feels pinched or painful.",),
    ),
    "mobility_floor": _template(
        "is a floor-based mobility drill for controlled movement through the named joints.",
        (
            "Use a comfortable floor surface and begin in a stable, pain-free range.",
            "Begin within an easy, pain-free range.",
        ),
        (
            "Move slowly through the drill while breathing normally.",
            "Pause briefly where the stretch or rotation feels useful, then return.",
        ),
        (
            "Keep the movement smooth rather than forcing the end range.",
            "Let the targeted joint move while the rest of the body stays quiet.",
        ),
        ("Bouncing into the stretch.", "Using a larger range than can be controlled."),
        (
            "Mobility work should feel gentle; back off if there is sharp pain or numbness.",
        ),
    ),
    "mobility_shoulder": _template(
        "improves controlled shoulder and upper-back motion with light resistance or body support.",
        (
            "Stand tall with the ribs stacked before moving the arms.",
            "Set the ribs over the pelvis before moving the arms.",
        ),
        (
            "Move the arms slowly without forcing the available shoulder range.",
            "Return before the shoulders compensate or the ribs flare.",
        ),
        ("Keep the neck relaxed.", "Use the largest smooth range available today."),
        (
            "Forcing the hands farther than the shoulders allow.",
            "Arching the lower back to create extra range.",
        ),
        ("Use less tension or a smaller range if the shoulder feels pinched.",),
    ),
    "ball_core": _template(
        "is a stability-ball core exercise that adds an unstable support to controlled bracing.",
        (
            "Place the ball on a non-slip surface and transfer weight onto it gradually.",
            "Brace before transferring body weight onto the ball.",
        ),
        (
            "Keep trunk alignment as the body holds or moves against the ball.",
            "Return slowly and reset the ball before the next repetition.",
        ),
        (
            "Keep pressure centered on the ball.",
            "Use a range that keeps the ribs and pelvis connected.",
        ),
        (
            "Moving so far that the ball escapes the base of support.",
            "Letting the lower back sag.",
        ),
        (
            "Keep clear space around the ball and shorten the lever if balance is uncertain.",
        ),
    ),
    "shrug": _template(
        "is a loaded shrug that trains the upper traps through controlled shoulder elevation.",
        (
            "Stand tall while holding the resistance at arm's length.",
            "Stand tall with straight but unlocked elbows.",
        ),
        (
            "Lift the shoulders straight toward the ears.",
            "Pause briefly, then lower fully under control.",
        ),
        (
            "Keep the head and trunk still.",
            "Move the shoulders vertically rather than rolling them.",
        ),
        (
            "Circling the shoulders under load.",
            "Bending the elbows to shorten the movement.",
        ),
        (
            "Use straps only if appropriate and maintain a grip that can control the set-down.",
        ),
    ),
    "free_press": _template(
        "is a close-grip free-weight press that emphasizes the triceps and chest.",
        (
            "Set a stable bench and bring the bar into position over the chest.",
            "Take an even close grip that keeps the wrists comfortable.",
        ),
        (
            "Lower the bar under control with the elbows near the torso.",
            "Press to straight arms while both sides rise together.",
        ),
        (
            "Stack the wrists over the forearms.",
            "Keep the shoulders supported by the bench.",
        ),
        (
            "Using a grip so narrow that the wrists bend sharply.",
            "Letting one end of the bar lead the press.",
        ),
        ("Use a load you can place into and out of the bench position safely.",),
    ),
    "pullover": _template(
        "trains the lats and chest as one dumbbell moves through a controlled overhead arc.",
        (
            "Lie securely on the bench with both feet planted.",
            "Hold one dumbbell over the chest with both hands and elbows softly bent.",
        ),
        (
            "Arc the dumbbell behind the head while keeping the ribs controlled.",
            "Pull it back over the chest without changing the elbow angle much.",
        ),
        (
            "Keep the hips and ribs quiet.",
            "Use only the shoulder range available without strain.",
        ),
        (
            "Turning the movement into an elbow extension.",
            "Lowering so far that the back arches off the bench.",
        ),
        (
            "Use a secure two-hand grip and a load that can be brought over the face safely.",
        ),
    ),
    "rollout": _template(
        "is a rollout that trains the core to resist extension as the arms travel forward.",
        (
            "Kneel on padding with the bar directly in front.",
            "Brace the trunk and begin with the shoulders supported over it.",
        ),
        (
            "Roll forward slowly while the hips and ribs remain connected.",
            "Pull back to the start before the lower back sags.",
        ),
        (
            "Move the shoulders and hips together.",
            "Use a shorter rollout than the maximum controllable range.",
        ),
        (
            "Reaching farther after the trunk position is lost.",
            "Sitting the hips back instead of pulling the implement in.",
        ),
        (
            "Keep the rolling path clear and use plates that rotate smoothly without slipping sideways.",
        ),
    ),
    "band_cable_hinge": _template(
        "is an anchored-resistance hip hinge for the glutes and hamstrings.",
        (
            "Secure the resistance and take light tension before hinging.",
            "Take tension with soft knees and a braced trunk.",
        ),
        (
            "Push the hips back while the resistance follows a close, controlled path.",
            "Stand by extending the hips without leaning backward.",
        ),
        (
            "Keep the feet planted and spine long.",
            "Let the hips, not the shoulders, start the motion.",
        ),
        (
            "Turning the hinge into a squat.",
            "Allowing the resistance to pull the body off balance.",
        ),
        (
            "Check the anchor and use resistance that can be controlled at full stretch.",
        ),
    ),
    "band_squat": _template(
        "is a band-resisted squat that increases tension as the legs straighten.",
        (
            "Stand evenly on the middle of the band.",
            "Hold the ends securely at shoulder height and set a balanced squat stance.",
        ),
        (
            "Squat while the band remains centered under both feet.",
            "Stand against the rising tension without letting the hands drop.",
        ),
        ("Keep both feet firmly on the band.", "Track the knees with the toes."),
        (
            "Using uneven band length between sides.",
            "Letting the band pull the torso forward.",
        ),
        ("Inspect the band and keep it away from the face if a foot could slip.",),
    ),
    "band_cable_lunge": _template(
        "is an anchored-resistance single-leg pattern that adds directional pull to the legs and trunk.",
        (
            "Secure the anchor and take tension before loading the working leg.",
            "Take a stable split or stepping stance with clear floor space.",
        ),
        (
            "Lower through the working leg while controlling the pull from the anchor.",
            "Drive through the working foot and return without being pulled off line.",
        ),
        (
            "Keep the hips and shoulders square.",
            "Maintain full-foot pressure on the working side.",
        ),
        (
            "Choosing resistance that disrupts balance.",
            "Letting the anchor pull the knee inward.",
        ),
        (
            "Confirm the anchor is secure and reduce resistance if the return cannot be controlled.",
        ),
    ),
    "cable_kickback": _template(
        "is a cable hip-extension exercise that isolates one glute while the trunk stays supported.",
        (
            "Attach the ankle cuff securely and face the cable stack.",
            "Hold the frame lightly and brace with the working leg slightly forward.",
        ),
        (
            "Drive the cuffed leg back from the hip without swinging.",
            "Return until the foot is under the body while maintaining cable tension.",
        ),
        (
            "Keep the pelvis facing the cable stack.",
            "Use a small hip-driven range with a quiet lower back.",
        ),
        (
            "Arching the back to move the leg farther.",
            "Turning the foot and pelvis open.",
        ),
        ("Check the cuff and cable before loading the working leg.",),
    ),
    "band_walk": _template(
        "is a band-resisted stepping drill for the glutes and hip stabilizers.",
        (
            "Place the band just above the knees and begin with light outward tension.",
            "Take a shallow athletic stance with tension already on the band.",
        ),
        (
            "Step under control while keeping the knees apart.",
            "Bring the trailing foot in only far enough to keep band tension.",
        ),
        (
            "Keep the toes and knees facing the same direction.",
            "Stay level rather than bobbing with each step.",
        ),
        (
            "Letting the feet snap together.",
            "Turning the toes outward to avoid hip effort.",
        ),
        ("Use a band tension that allows controlled foot placement.",),
    ),
    "cable_crunch": _template(
        "is a kneeling cable crunch that trains controlled spinal flexion against resistance.",
        (
            "Kneel facing the stack with the rope held beside the head.",
            "Set the hips over the knees and take tension before bracing.",
        ),
        (
            "Curl the ribs toward the pelvis while the hips remain nearly still.",
            "Return slowly until the trunk is tall without letting the stack pull the spine open.",
        ),
        (
            "Move through the trunk rather than sitting back.",
            "Keep the rope quiet beside the head.",
        ),
        ("Pulling with the arms.", "Hinging at the hips instead of curling the torso."),
        (
            "Use padding for the knees and a load that does not pull you toward the stack.",
        ),
    ),
    "high_pull": _template(
        "is an explosive barbell pull for the hips, upper back, and traps without a catch.",
        (
            "Hold the bar in front of the thighs with an even overhand grip.",
            "Set the feet, hinge slightly, and brace before accelerating.",
        ),
        (
            "Extend the hips and knees to drive the bar upward close to the body.",
            "Guide the elbows high, then lower and reset under control.",
        ),
        (
            "Keep the bar close throughout the pull.",
            "Let the legs and hips create the acceleration before the arms guide it.",
        ),
        ("Reverse-curling the bar slowly.", "Pulling the bar far away from the torso."),
        ("Use open space and a light enough load to control the lowering phase.",),
    ),
    "prone_shoulder": _template(
        "is a prone shoulder-control drill for the upper back, rear shoulders, and rotator cuff.",
        (
            "Lie face down on a comfortable surface with the forehead supported.",
            "Begin with the arms in the first Y position and no external load.",
        ),
        (
            "Lift the hands and arms slightly using the upper back.",
            "Lower softly before moving to the next arm position.",
        ),
        (
            "Keep the neck long and ribs on the floor.",
            "Use a small lift with the thumbs pointing upward.",
        ),
        (
            "Trying to lift the arms as high as possible.",
            "Shrugging the shoulders toward the ears.",
        ),
        ("Keep the range gentle and stop if the front of the shoulder feels pinched.",),
    ),
    "band_pull_apart": _template(
        "is an unanchored band pull for the rear shoulders and upper back.",
        (
            "Hold the band in front of the chest with straight arms and light tension.",
            "Choose a grip width that allows the arms to open without shrugging.",
        ),
        (
            "Pull the hands apart until the band approaches the chest.",
            "Return slowly to the starting tension without letting the band snap back.",
        ),
        (
            "Keep the elbows soft but nearly straight.",
            "Move the shoulder blades without flaring the ribs.",
        ),
        (
            "Using a band too heavy to open fully.",
            "Bending the elbows to shorten the pull.",
        ),
        ("Inspect the band and keep it away from the face if the grip slips.",),
    ),
}


_SEED_DEFINITIONS: tuple[_SeedDefinition, ...] = (
    _SeedDefinition(
        "Push-Up",
        "push_up",
        "Lower the chest toward the floor and press back to a full plank.",
    ),
    _SeedDefinition(
        "Incline Push-Up",
        "push_up",
        "Keep the hands on the bench and move the chest toward its front edge.",
    ),
    _SeedDefinition(
        "Bodyweight Squat",
        "squat_body",
        "Reach the arms forward as needed for balance while sitting between the feet.",
    ),
    _SeedDefinition(
        "Reverse Lunge",
        "lunge_body",
        "Step backward, lower the rear knee, then drive through the front foot to return.",
    ),
    _SeedDefinition(
        "Split Squat",
        "lunge_body",
        "Keep the split stance fixed as the body travels straight down and up.",
    ),
    _SeedDefinition(
        "Glute Bridge",
        "bridge",
        "Press from the floor until the hips are level with the thighs and torso.",
    ),
    _SeedDefinition(
        "Plank",
        "plank",
        "Hold a still forearm plank for the planned interval.",
    ),
    _SeedDefinition(
        "Side Plank",
        "plank",
        "Stack the hips and shoulders while supporting the body on one forearm.",
    ),
    _SeedDefinition(
        "Dead Bug",
        "floor_core",
        "Lower the opposite arm and leg while the other limbs remain over the torso.",
    ),
    _SeedDefinition(
        "Mountain Climber",
        "body_conditioning",
        "Alternate driving one knee toward the chest from a strong plank position.",
    ),
    _SeedDefinition(
        "Inverted Row",
        "supported_row",
        "Pull the chest toward the bar while the heels and body line stay fixed.",
    ),
    _SeedDefinition(
        "Dumbbell Bench Press",
        "db_press",
        "Press both dumbbells vertically from a flat-bench position.",
    ),
    _SeedDefinition(
        "Incline Dumbbell Press",
        "db_press",
        "Use an inclined bench and press upward over the upper chest.",
    ),
    _SeedDefinition(
        "Dumbbell Shoulder Press",
        "shoulder_press",
        "Press the dumbbells from shoulder level without bringing them together forcefully.",
    ),
    _SeedDefinition(
        "One-Arm Dumbbell Row",
        "db_row",
        "Brace one hand on the bench and row the free-side elbow toward the hip.",
    ),
    _SeedDefinition(
        "Dumbbell Row",
        "db_row",
        "Hold the hinge steady while rowing both dumbbells beside the ribs.",
    ),
    _SeedDefinition(
        "Chest-Supported Dumbbell Row",
        "db_row",
        "Keep the chest on the inclined bench while pulling both elbows back.",
    ),
    _SeedDefinition(
        "Chest-Supported Row",
        "supported_row",
        "Stay connected to the bench while drawing the dumbbells toward the lower ribs.",
    ),
    _SeedDefinition(
        "Dumbbell RDL",
        "hinge_db",
        "Lower the dumbbells along the thighs and shins until the hamstrings limit the hinge.",
    ),
    _SeedDefinition(
        "Goblet Squat",
        "squat_db",
        "Hold one dumbbell at the chest and sit down between the knees.",
    ),
    _SeedDefinition(
        "Dumbbell Split Squat",
        "lunge_loaded",
        "Keep the dumbbells at the sides while moving vertically in a fixed split stance.",
    ),
    _SeedDefinition(
        "Dumbbell Reverse Lunge",
        "lunge_loaded",
        "Step one foot back with the dumbbells quiet at the sides, then return through the front leg.",
    ),
    _SeedDefinition(
        "Dumbbell Lateral Raise",
        "raise",
        "Raise the dumbbells out to the sides until the arms approach shoulder height.",
    ),
    _SeedDefinition(
        "Dumbbell Curl",
        "curl",
        "Turn the palms forward and curl both dumbbells without moving the upper arms.",
    ),
    _SeedDefinition(
        "Dumbbell Triceps Extension",
        "triceps",
        "Hold one dumbbell overhead with both hands and straighten the elbows without widening them.",
    ),
    _SeedDefinition(
        "Farmer Carry",
        "carry",
        "Carry equal dumbbells at both sides while staying tall and level.",
    ),
    _SeedDefinition(
        "Barbell Squat",
        "squat_barbell",
        "Keep the bar balanced across the upper back as the hips and knees bend together.",
    ),
    _SeedDefinition(
        "Back Squat",
        "squat_barbell",
        "Set the bar securely on the upper back and stand by driving the shoulders and hips together.",
    ),
    _SeedDefinition(
        "Front Squat",
        "squat_barbell",
        "Keep the elbows lifted so the bar stays on the front of the shoulders.",
    ),
    _SeedDefinition(
        "Barbell Bench Press",
        "barbell_press",
        "Lower the bar to a repeatable mid-chest touch point and press it back over the shoulders.",
    ),
    _SeedDefinition(
        "Overhead Press",
        "shoulder_press",
        "Move the head slightly back for the bar, then finish with the bar stacked overhead.",
    ),
    _SeedDefinition(
        "Barbell Row",
        "barbell_row",
        "Row the bar toward the lower ribs while preserving the original hip hinge.",
    ),
    _SeedDefinition(
        "Romanian Deadlift",
        "hinge_barbell",
        "Begin from standing and lower the bar only as far as the hamstrings allow.",
    ),
    _SeedDefinition(
        "Conventional Deadlift",
        "deadlift",
        "Reset the brace from the floor before each pull rather than bouncing repetitions.",
    ),
    _SeedDefinition(
        "Hip Thrust",
        "bridge",
        "Use the bench edge beneath the upper back and finish with the shins close to vertical.",
    ),
    _SeedDefinition(
        "EZ-Bar Curl",
        "curl",
        "Use the angled grips to curl the bar while keeping both elbows near the sides.",
    ),
    _SeedDefinition(
        "EZ-Bar Skull Crusher",
        "triceps",
        "Lower the bar toward the forehead by bending only the elbows, then extend it away.",
    ),
    _SeedDefinition(
        "EZ-Bar Close-Grip Press",
        "free_press",
        "Keep the hands close on the EZ-bar and press from the bench with the elbows near the torso.",
    ),
    _SeedDefinition(
        "Pull-Up",
        "pull_up",
        "Use an overhand grip and pull until the chin clears the bar without reaching the neck forward.",
    ),
    _SeedDefinition(
        "Chin-Up",
        "pull_up",
        "Use an underhand grip and pull the chest toward the bar with the elbows close.",
    ),
    _SeedDefinition(
        "Band-Assisted Pull-Up",
        "pull_up",
        "Place one knee in the band and let it assist without bouncing out of the bottom.",
    ),
    _SeedDefinition(
        "Hanging Knee Raise",
        "hanging_core",
        "Bend the knees and lift them toward the chest without swinging the torso.",
    ),
    _SeedDefinition(
        "Band Pull-Apart",
        "band_pull_apart",
        "Stretch the band across the chest until the arms form a straight line.",
    ),
    _SeedDefinition(
        "Band Face Pull",
        "face_pull",
        "Pull the band toward eyebrow height while separating the hands.",
    ),
    _SeedDefinition(
        "Band Row",
        "supported_row",
        "Pull the anchored band toward the ribs and control it back to straight arms.",
    ),
    _SeedDefinition(
        "Band Triceps Pressdown",
        "triceps",
        "Keep the elbows by the sides while pressing the anchored band toward the thighs.",
    ),
    _SeedDefinition(
        "Band External Rotation",
        "shoulder_rotation",
        "Rotate the forearm away from the anchor while the elbow stays tucked at the side.",
    ),
    _SeedDefinition(
        "Cable Row",
        "cable_row",
        "Sit facing the cable stack and pull the handle toward the lower ribs without rocking backward.",
    ),
    _SeedDefinition(
        "Cable Lat Pulldown",
        "pulldown",
        "Pull the cable handle to the upper chest while keeping the torso nearly upright.",
    ),
    _SeedDefinition(
        "Lat Pulldown",
        "pulldown",
        "Bring the bar toward the upper chest with a grip that lets the elbows track down.",
    ),
    _SeedDefinition(
        "Cable Face Pull",
        "face_pull",
        "Pull the cable attachment toward the face and finish with the hands outside the elbows.",
    ),
    _SeedDefinition(
        "Cable Triceps Pressdown",
        "triceps",
        "Press the cable handle to the thighs while the upper arms remain still.",
    ),
    _SeedDefinition(
        "Cable Curl",
        "curl",
        "Curl the cable handle without stepping closer as the resistance rises.",
    ),
    _SeedDefinition(
        "Cable Lateral Raise",
        "raise",
        "Stand side-on with the low cable behind the legs and raise the outside arm to shoulder height.",
    ),
    _SeedDefinition(
        "Cable Woodchop",
        "anti_rotation",
        "Guide the handle diagonally across the body while the hips and torso rotate together under control.",
    ),
    _SeedDefinition(
        "Leg Press",
        "squat_supported",
        "Lower the sled until the knees reach a comfortable bend, then press without lifting the hips.",
    ),
    _SeedDefinition(
        "Machine Chest Press",
        "cable_press",
        "Press the machine handles forward while the back stays against the pad.",
    ),
    _SeedDefinition(
        "Machine Row",
        "supported_row",
        "Keep the chest against the machine pad while pulling both handles toward the ribs.",
    ),
    _SeedDefinition(
        "Treadmill Walk",
        "treadmill",
        "Use a level or modest incline and a pace that permits a natural walking stride.",
    ),
    _SeedDefinition(
        "Treadmill Incline Walk",
        "treadmill",
        "Raise the incline gradually while keeping a walking pace that does not require the rails.",
    ),
    _SeedDefinition(
        "Treadmill Intervals",
        "treadmill",
        "Alternate planned faster bouts with slower recovery periods after the belt settles.",
    ),
    _SeedDefinition(
        "Bike Steady State",
        "bike",
        "Hold a consistent cadence and moderate resistance for the full steady interval.",
    ),
    _SeedDefinition(
        "Bike Intervals",
        "bike",
        "Alternate controlled hard efforts with easy pedaling recoveries.",
    ),
    _SeedDefinition(
        "Bear Crawl",
        "body_conditioning",
        "Crawl on hands and feet with the knees hovering just above the floor.",
    ),
    _SeedDefinition(
        "Bird Dog",
        "floor_core",
        "Reach the opposite arm and leg long from all fours without shifting the hips.",
    ),
    _SeedDefinition(
        "Hollow Body Hold",
        "floor_core",
        "Hold the shoulders and legs off the floor while keeping the lower back gently pressed down.",
    ),
    _SeedDefinition(
        "Hollow Rock",
        "floor_core",
        "Rock the rigid hollow shape from shoulders to hips without changing the body position.",
    ),
    _SeedDefinition(
        "Superman Hold",
        "floor_core",
        "Lift the arms and legs only slightly while keeping the neck in line with the spine.",
    ),
    _SeedDefinition(
        "Walking Lunge",
        "lunge_body",
        "Step forward into each lunge and bring the rear leg through into the next stride.",
    ),
    _SeedDefinition(
        "Lateral Lunge",
        "lunge_body",
        "Step sideways, sit into the stepping hip, and keep the other leg long.",
    ),
    _SeedDefinition(
        "Wall Sit",
        "squat_supported",
        "Slide down the wall and hold a knee angle that can be maintained without shifting.",
    ),
    _SeedDefinition(
        "Standing Calf Raise",
        "calf_foot",
        "Rise onto the balls of both feet, pause at the top, and lower the heels slowly.",
    ),
    _SeedDefinition(
        "Single-Leg Glute Bridge",
        "bridge",
        "Keep one thigh lifted while the planted leg raises and lowers the hips level.",
    ),
    _SeedDefinition(
        "Pike Push-Up",
        "pike_press",
        "Lower the head forward between the hands and press back while the hips remain high.",
    ),
    _SeedDefinition(
        "Close-Grip Push-Up",
        "push_up",
        "Place the hands closer than shoulder width and keep the elbows near the torso.",
    ),
    _SeedDefinition(
        "Tempo Push-Up",
        "push_up",
        "Follow the planned slow lowering and pause before pressing up without bouncing.",
    ),
    _SeedDefinition(
        "Decline Push-Up",
        "push_up",
        "Place the feet securely on the bench and lower the upper chest toward the floor.",
    ),
    _SeedDefinition(
        "Bench Dip",
        "dip",
        "Bend the elbows straight back and press up before the shoulders roll forward.",
    ),
    _SeedDefinition(
        "Dumbbell Floor Press",
        "floor_press",
        "Press both dumbbells from the floor while the upper arms touch down softly.",
    ),
    _SeedDefinition(
        "Dumbbell Fly",
        "chest_fly",
        "Open the dumbbells from above the chest in a wide arc on a flat bench.",
    ),
    _SeedDefinition(
        "Incline Dumbbell Fly",
        "chest_fly",
        "Use an inclined bench and open the dumbbells in line with the upper chest.",
    ),
    _SeedDefinition(
        "Dumbbell Pullover",
        "pullover",
        "Hold one dumbbell over the chest and arc it behind the head only as far as the ribs stay down.",
    ),
    _SeedDefinition(
        "Arnold Press",
        "shoulder_press",
        "Rotate the palms outward as the dumbbells travel from in front of the shoulders to overhead.",
    ),
    _SeedDefinition(
        "Seated Dumbbell Shoulder Press",
        "shoulder_press",
        "Stay against the bench support while pressing both dumbbells overhead.",
    ),
    _SeedDefinition(
        "Dumbbell Front Raise",
        "raise",
        "Raise the dumbbells forward to shoulder height without leaning back.",
    ),
    _SeedDefinition(
        "Dumbbell Rear Delt Fly",
        "rear_delt",
        "Hold a hip hinge and open the dumbbells wide without pulling them toward the ribs.",
    ),
    _SeedDefinition(
        "Chest-Supported Rear Delt Fly",
        "rear_delt",
        "Keep the chest on the incline bench while sweeping the arms out wide.",
    ),
    _SeedDefinition(
        "Dumbbell Shrug",
        "shrug",
        "Raise both shoulders vertically while the dumbbells remain at the sides.",
    ),
    _SeedDefinition(
        "Dumbbell Upright Row",
        "upright_row",
        "Pull both dumbbells upward close to the torso and stop below any shoulder pinch.",
    ),
    _SeedDefinition(
        "Dumbbell Hammer Curl",
        "curl",
        "Keep the palms facing each other throughout the curl.",
    ),
    _SeedDefinition(
        "Dumbbell Concentration Curl",
        "curl",
        "Brace the upper arm against the inner thigh and curl without lifting the elbow.",
    ),
    _SeedDefinition(
        "Dumbbell Zottman Curl",
        "curl",
        "Curl palms-up, rotate palms-down at the top, and lower slowly.",
    ),
    _SeedDefinition(
        "Dumbbell Kickback",
        "triceps",
        "Hold the upper arm beside the torso and straighten the elbow behind you.",
    ),
    _SeedDefinition(
        "Dumbbell Skull Crusher",
        "triceps",
        "Lower the dumbbells beside the forehead and extend them without moving the shoulders.",
    ),
    _SeedDefinition(
        "Dumbbell Close-Grip Press",
        "db_press",
        "Press the dumbbells together over the chest while keeping the elbows near the sides.",
    ),
    _SeedDefinition(
        "Dumbbell Step-Up",
        "lunge_loaded",
        "Plant the whole foot on the bench and stand through the top leg without pushing off the floor.",
    ),
    _SeedDefinition(
        "Dumbbell Lateral Lunge",
        "lunge_loaded",
        "Step sideways with the dumbbells controlled and sit into the stepping hip.",
    ),
    _SeedDefinition(
        "Dumbbell Bulgarian Split Squat",
        "lunge_loaded",
        "Rest the rear foot on the bench and lower through the front leg without drifting forward.",
    ),
    _SeedDefinition(
        "Dumbbell Sumo Squat",
        "squat_db",
        "Use a wide stance and hold the dumbbell between the legs as the knees track outward.",
    ),
    _SeedDefinition(
        "Dumbbell Front Squat",
        "squat_db",
        "Rack the dumbbells at the shoulders and keep the elbows lifted while squatting.",
    ),
    _SeedDefinition(
        "Dumbbell Single-Leg RDL",
        "hinge_db",
        "Hinge over one planted leg while the free leg reaches back and the hips stay square.",
    ),
    _SeedDefinition(
        "Dumbbell Hip Thrust",
        "bridge",
        "Center the dumbbell across the hips and drive up from the bench-supported position.",
    ),
    _SeedDefinition(
        "Suitcase Carry",
        "carry",
        "Carry one dumbbell at the side without leaning toward or away from it.",
    ),
    _SeedDefinition(
        "Waiter Carry",
        "carry",
        "Carry one dumbbell locked out overhead while the shoulder stays stacked and stable.",
    ),
    _SeedDefinition(
        "Dumbbell Front Rack Carry",
        "carry",
        "Hold the dumbbells at the shoulders and walk without letting the elbows or ribs flare.",
    ),
    _SeedDefinition(
        "Dumbbell Calf Raise",
        "calf_foot",
        "Hold the dumbbells at the sides while rising and lowering through the ankles.",
    ),
    _SeedDefinition(
        "Pause Squat",
        "squat_barbell",
        "Pause motionless at the planned depth, then drive up without relaxing the brace.",
    ),
    _SeedDefinition(
        "Box Squat",
        "squat_barbell",
        "Reach the hips back to a controlled touch on the bench, then stand without rocking.",
    ),
    _SeedDefinition(
        "Barbell Reverse Lunge",
        "lunge_loaded",
        "Keep the bar level across the upper back while stepping backward into each repetition.",
    ),
    _SeedDefinition(
        "Barbell Split Squat",
        "lunge_loaded",
        "Set a fixed split stance under the bar and move vertically through the front leg.",
    ),
    _SeedDefinition(
        "Barbell Good Morning",
        "hinge_barbell",
        "Keep the bar on the upper back as the hips travel behind the heels.",
    ),
    _SeedDefinition(
        "Barbell Glute Bridge",
        "bridge",
        "Hold the bar securely across the hips and press up from the floor.",
    ),
    _SeedDefinition(
        "Barbell Floor Press",
        "floor_press",
        "Lower the bar until both upper arms meet the floor evenly, then press.",
    ),
    _SeedDefinition(
        "Close-Grip Bench Press",
        "barbell_press",
        "Use a shoulder-width grip and keep the elbows close during the press.",
    ),
    _SeedDefinition(
        "Incline Barbell Bench Press",
        "barbell_press",
        "Set the bench to an incline and lower the bar toward the upper chest.",
    ),
    _SeedDefinition(
        "Push Press",
        "push_press",
        "Use one short knee dip and leg drive before finishing the bar overhead.",
    ),
    _SeedDefinition(
        "Pendlay Row",
        "barbell_row",
        "Start each repetition from a settled bar on the floor and pull toward the lower ribs.",
    ),
    _SeedDefinition(
        "Barbell High Pull",
        "high_pull",
        "Extend the hips and guide the bar upward with high elbows without trying to catch it.",
    ),
    _SeedDefinition(
        "Barbell Curl",
        "curl",
        "Curl the straight bar while the upper arms stay vertical and both wrists remain comfortable.",
    ),
    _SeedDefinition(
        "Barbell Rollout",
        "rollout",
        "Roll the bar forward from the knees only as far as the trunk stays braced, then pull it back.",
    ),
    _SeedDefinition(
        "Plate Front Raise",
        "raise",
        "Hold one plate with both hands and raise it forward to shoulder height.",
    ),
    _SeedDefinition(
        "Plate Curl",
        "curl",
        "Grip the sides of one plate and curl it without letting the wrists fold.",
    ),
    _SeedDefinition(
        "Plate Pinch Carry",
        "carry",
        "Pinch the smooth sides of the plates and walk before the grip begins to slip.",
    ),
    _SeedDefinition(
        "EZ-Bar Reverse Curl",
        "curl",
        "Use a palms-down grip and keep the wrists straight as the EZ-bar rises.",
    ),
    _SeedDefinition(
        "EZ-Bar Preacher-Style Curl",
        "curl",
        "Brace the upper arms against the inclined bench and curl without lifting them away.",
    ),
    _SeedDefinition(
        "EZ-Bar Overhead Triceps Extension",
        "triceps",
        "Hold the EZ-bar overhead and bend it behind the head while the elbows stay forward.",
    ),
    _SeedDefinition(
        "EZ-Bar Upright Row",
        "upright_row",
        "Pull the EZ-bar close to the torso and stop when the elbows reach a comfortable height.",
    ),
    _SeedDefinition(
        "Neutral-Grip Pull-Up",
        "pull_up",
        "Use the parallel handles and pull with the elbows tracking close to the ribs.",
    ),
    _SeedDefinition(
        "Negative Pull-Up",
        "pull_up",
        "Step to the top position and lower for the planned count before resetting with the step.",
    ),
    _SeedDefinition(
        "Scapular Pull-Up",
        "pull_up",
        "Keep the elbows straight and lift the body slightly by drawing the shoulder blades down.",
    ),
    _SeedDefinition(
        "Commando Pull-Up",
        "pull_up",
        "Use a staggered grip and pull one shoulder toward each side of the bar in turn.",
    ),
    _SeedDefinition(
        "Dead Hang",
        "hang",
        "Hang with straight arms for the planned time while keeping the shoulders comfortable.",
    ),
    _SeedDefinition(
        "Hanging Leg Raise",
        "hanging_core",
        "Keep the legs long as they lift forward, using only the height you can control without swinging.",
    ),
    _SeedDefinition(
        "Hanging Oblique Knee Raise",
        "hanging_core",
        "Lift the bent knees toward one side of the torso and alternate sides without twisting from momentum.",
    ),
    _SeedDefinition(
        "Band Biceps Curl",
        "curl",
        "Stand on the band evenly and curl the handles while maintaining tension at the bottom.",
    ),
    _SeedDefinition(
        "Band Hammer Curl",
        "curl",
        "Use a neutral grip on the band and curl with the thumbs staying upward.",
    ),
    _SeedDefinition(
        "Band Overhead Triceps Extension",
        "triceps",
        "Anchor the band low behind you and straighten the elbows overhead.",
    ),
    _SeedDefinition(
        "Band Lateral Raise",
        "raise",
        "Stand on the band and raise the arms outward without shifting the feet.",
    ),
    _SeedDefinition(
        "Band Shoulder Press",
        "shoulder_press",
        "Stand securely on the band and press the handles from the shoulders overhead.",
    ),
    _SeedDefinition(
        "Band Lat Pulldown",
        "pulldown",
        "Kneel below the anchor and pull both ends of the band toward the shoulders.",
    ),
    _SeedDefinition(
        "Band Straight-Arm Pulldown",
        "straight_arm_pull",
        "Sweep the band from overhead to the thighs while the elbows remain nearly straight.",
    ),
    _SeedDefinition(
        "Band Pull-Through",
        "band_cable_hinge",
        "Face away from the low anchor, hinge with the band between the legs, and stand through the hips.",
    ),
    _SeedDefinition(
        "Band Good Morning",
        "band_cable_hinge",
        "Loop the band under the feet and behind the shoulders, then hinge without letting it pull the chest down.",
    ),
    _SeedDefinition(
        "Band Resisted Push-Up",
        "push_up",
        "Run the band across the upper back and press against its rising tension.",
    ),
    _SeedDefinition(
        "Band Pallof Press",
        "anti_rotation",
        "Press the band straight from the chest and pause without turning toward the anchor.",
    ),
    _SeedDefinition(
        "Band Woodchop",
        "anti_rotation",
        "Guide the band diagonally across the body while controlling the return toward the anchor.",
    ),
    _SeedDefinition(
        "Band Lateral Walk",
        "band_walk",
        "Keep band tension as you step sideways without bringing the feet fully together.",
    ),
    _SeedDefinition(
        "Band Monster Walk",
        "band_walk",
        "Take diagonal forward steps while the knees continue pressing against the band.",
    ),
    _SeedDefinition(
        "Band Glute Bridge",
        "bridge",
        "Press the knees gently out against the band while raising the hips.",
    ),
    _SeedDefinition(
        "Single-Arm Cable Row",
        "cable_row",
        "Row one handle toward the ribs without letting the torso rotate toward the cable.",
    ),
    _SeedDefinition(
        "Cable High Row",
        "cable_row",
        "Pull from a high cable angle toward the upper chest with the elbows traveling back and down.",
    ),
    _SeedDefinition(
        "Cable Reverse Fly",
        "rear_delt",
        "Hold one cable handle in each hand and open the arms wide with a soft elbow bend.",
    ),
    _SeedDefinition(
        "Cable Chest Fly",
        "chest_fly",
        "Bring the cable handles together in front of the chest while keeping the elbow angle steady.",
    ),
    _SeedDefinition(
        "Single-Arm Cable Press",
        "cable_press",
        "Press one handle forward without allowing the trunk to rotate away from the cable.",
    ),
    _SeedDefinition(
        "Cable Upright Row",
        "upright_row",
        "Pull the low cable handle upward close to the torso and stop at a comfortable height.",
    ),
    _SeedDefinition(
        "Cable Y Raise",
        "raise",
        "Raise the cable handles on a diagonal into a Y shape with the thumbs leading.",
    ),
    _SeedDefinition(
        "Cable External Rotation",
        "shoulder_rotation",
        "Rotate the forearm away from the cable while the elbow remains near the side.",
    ),
    _SeedDefinition(
        "Cable Internal Rotation",
        "shoulder_rotation",
        "Rotate the forearm toward the torso while the elbow stays fixed beside the ribs.",
    ),
    _SeedDefinition(
        "Cable Pull-Through",
        "band_cable_hinge",
        "Face away from the low rope cable, hinge it between the legs, and stand by extending the hips.",
    ),
    _SeedDefinition(
        "Cable Crunch",
        "cable_crunch",
        "Kneel with the rope by the head and curl the ribs toward the pelvis without sitting the hips back.",
    ),
    _SeedDefinition(
        "Cable Pallof Press",
        "anti_rotation",
        "Press the cable handle away from the chest and pause while staying square.",
    ),
    _SeedDefinition(
        "Rope Triceps Pressdown",
        "triceps",
        "Press the rope down and separate its ends slightly at full elbow extension.",
    ),
    _SeedDefinition(
        "Rope Overhead Triceps Extension",
        "triceps",
        "Face away from the cable and extend the rope forward overhead while the upper arms stay still.",
    ),
    _SeedDefinition(
        "Rope Hammer Curl",
        "curl",
        "Curl the rope with a neutral grip and separate the ends slightly near the top.",
    ),
    _SeedDefinition(
        "Rope Face Pull",
        "face_pull",
        "Pull the rope toward the face and finish with one end beside each ear.",
    ),
    _SeedDefinition(
        "Straight-Arm Cable Pulldown",
        "straight_arm_pull",
        "Pull the cable bar from overhead to the thighs without turning it into a row.",
    ),
    _SeedDefinition(
        "Stability Ball Hamstring Curl",
        "hamstring_curl",
        "Lift the hips and roll the ball toward the body by bending both knees.",
    ),
    _SeedDefinition(
        "Stability Ball Rollout",
        "ball_core",
        "Roll the ball forward from the forearms while the hips and ribs stay aligned.",
    ),
    _SeedDefinition(
        "Stability Ball Plank",
        "ball_core",
        "Hold a plank with the forearms on the ball and the feet set wide enough for control.",
    ),
    _SeedDefinition(
        "Stability Ball Stir-the-Pot",
        "ball_core",
        "Draw small circles with the forearms on the ball without rotating the hips.",
    ),
    _SeedDefinition(
        "Stability Ball Wall Squat",
        "squat_supported",
        "Keep the ball between the back and wall as it rolls during the squat.",
    ),
    _SeedDefinition(
        "Stability Ball Dead Bug",
        "floor_core",
        "Press the ball between opposite limbs while the free arm and leg extend.",
    ),
    _SeedDefinition(
        "Treadmill Easy Jog",
        "treadmill",
        "Jog at a conversational effort with a short, relaxed stride.",
    ),
    _SeedDefinition(
        "Treadmill Hill Intervals",
        "treadmill",
        "Alternate higher-incline work periods with lower-incline recovery after speed is controlled.",
    ),
    _SeedDefinition(
        "Treadmill Tempo Run",
        "treadmill",
        "Build to a steady challenging pace that remains controlled for the planned tempo block.",
    ),
    _SeedDefinition(
        "Bike Recovery Ride",
        "bike",
        "Use very light resistance and an easy cadence that feels restorative rather than demanding.",
    ),
    _SeedDefinition(
        "Bike Tempo Ride",
        "bike",
        "Hold a purposeful steady cadence and resistance for the planned tempo duration.",
    ),
    _SeedDefinition(
        "Bike Hill Intervals",
        "bike",
        "Increase resistance for each hill effort while keeping the pedal stroke smooth.",
    ),
    _SeedDefinition(
        "Wall Push-Up",
        "push_up",
        "Lean toward the wall as one rigid unit and press back to standing.",
    ),
    _SeedDefinition(
        "Scapular Push-Up",
        "push_up",
        "Keep the elbows straight while the chest sinks slightly and then presses away through the shoulder blades.",
    ),
    _SeedDefinition(
        "Plank Shoulder Tap",
        "plank",
        "Lift one hand to tap the opposite shoulder while the hips remain as still as possible.",
    ),
    _SeedDefinition(
        "Reverse Crunch",
        "floor_core",
        "Curl the pelvis gently off the floor as the knees move toward the ribs.",
    ),
    _SeedDefinition(
        "Heel Tap",
        "floor_core",
        "Reach side to side toward each heel while the shoulders remain slightly lifted.",
    ),
    _SeedDefinition(
        "Side Plank Reach-Through",
        "plank",
        "Rotate the top arm under the ribs and reopen without letting the supporting shoulder collapse.",
    ),
    _SeedDefinition(
        "Seated Knee Tuck",
        "floor_core",
        "Lean back slightly and draw the knees toward the chest before extending them with control.",
    ),
    _SeedDefinition(
        "Toe Walk",
        "calf_foot",
        "Walk on the balls of the feet with the heels lifted and steps kept short.",
    ),
    _SeedDefinition(
        "Heel Walk",
        "calf_foot",
        "Lift the forefeet and walk on the heels without leaning the torso back.",
    ),
    _SeedDefinition(
        "Prone Y-T-W Raise",
        "prone_shoulder",
        "Lift the arms lightly through Y, T, and W shapes while the chest stays supported by the floor.",
    ),
    _SeedDefinition(
        "Cat-Cow",
        "mobility_floor",
        "Alternate gently rounding and extending the spine from an all-fours position.",
    ),
    _SeedDefinition(
        "Quadruped T-Spine Rotation",
        "mobility_floor",
        "Rotate one elbow toward the ceiling while the hips remain over the knees.",
    ),
    _SeedDefinition(
        "Half-Kneeling Hip Flexor Stretch",
        "mobility_floor",
        "Tuck the pelvis gently and shift forward until the front of the rear hip stretches.",
    ),
    _SeedDefinition(
        "90/90 Hip Switch",
        "mobility_floor",
        "Rotate both knees side to side between 90-degree hip positions without forcing the range.",
    ),
    _SeedDefinition(
        "Child's Pose Lat Stretch",
        "mobility_floor",
        "Reach both hands forward while the hips settle back toward the heels.",
    ),
    _SeedDefinition(
        "Wall Slide",
        "mobility_shoulder",
        "Slide the forearms upward on the wall without flaring the ribs or shrugging.",
    ),
    _SeedDefinition(
        "Dumbbell Squeeze Press",
        "db_press",
        "Keep the dumbbells pressed together as they lower and rise over the chest.",
    ),
    _SeedDefinition(
        "Low-Incline Dumbbell Press",
        "db_press",
        "Use a shallow bench incline and press over the upper-middle chest.",
    ),
    _SeedDefinition(
        "Dumbbell Tate Press",
        "triceps",
        "Lower the inside ends of the dumbbells toward the chest by bending the elbows outward.",
    ),
    _SeedDefinition(
        "Dumbbell Reverse Curl",
        "curl",
        "Keep the palms facing down while curling the dumbbells without bending the wrists.",
    ),
    _SeedDefinition(
        "Dumbbell Cross-Body Hammer Curl",
        "curl",
        "Curl one dumbbell toward the opposite side of the chest with a neutral wrist.",
    ),
    _SeedDefinition(
        "Dumbbell Spider Curl",
        "curl",
        "Lie chest-down on the incline bench and curl from arms hanging vertically.",
    ),
    _SeedDefinition(
        "Dumbbell Suitcase Deadlift",
        "hinge_db",
        "Start the dumbbells beside the feet and stand while keeping them close to the legs.",
    ),
    _SeedDefinition(
        "Dumbbell Farmer March",
        "carry",
        "March in place with equal dumbbells at the sides and pause briefly on each single-leg stance.",
    ),
    _SeedDefinition(
        "Dumbbell Suitcase March",
        "carry",
        "March in place with one dumbbell at the side while keeping the trunk level.",
    ),
    _SeedDefinition(
        "Dumbbell Tempo Goblet Squat",
        "squat_db",
        "Follow the planned slow descent and pause while the dumbbell stays at the chest.",
    ),
    _SeedDefinition(
        "Dumbbell Heel-Elevated Goblet Squat",
        "squat_db",
        "Place the heels securely on plates and keep the torso tall as the knees travel forward.",
    ),
    _SeedDefinition(
        "Dumbbell Offset Reverse Lunge",
        "lunge_loaded",
        "Hold the dumbbell on one side while stepping back without allowing the torso to lean.",
    ),
    _SeedDefinition(
        "Dumbbell Skater Squat",
        "lunge_loaded",
        "Reach the free leg behind and lower on the working leg toward a controlled target.",
    ),
    _SeedDefinition(
        "Dumbbell Renegade Row",
        "db_row",
        "Row one dumbbell from a wide-foot plank while the other hand presses into the floor.",
    ),
    _SeedDefinition(
        "Barbell Shrug",
        "shrug",
        "Raise both shoulders vertically while the bar remains close to the thighs.",
    ),
    _SeedDefinition(
        "Barbell Calf Raise",
        "calf_foot",
        "Hold the bar securely in the rack position and rise onto both forefeet without bending the knees.",
    ),
    _SeedDefinition(
        "Rack Pull",
        "hinge_barbell",
        "Start the bar from rack safeties just below knee height and stand without bouncing it.",
    ),
    _SeedDefinition(
        "Barbell Hip Hinge Drill",
        "hinge_barbell",
        "Use the light bar as feedback while pushing the hips back through a practice-range hinge.",
    ),
    _SeedDefinition(
        "Barbell Tall-Kneeling Press",
        "shoulder_press",
        "Press from both knees while the glutes and trunk prevent the body from leaning back.",
    ),
    _SeedDefinition(
        "Barbell Lunge",
        "lunge_loaded",
        "Step into each lunge with the bar balanced and enough stance width for stability.",
    ),
    _SeedDefinition(
        "Barbell Reverse-Grip Row",
        "barbell_row",
        "Use a palms-up grip and row toward the waist while the elbows stay close.",
    ),
    _SeedDefinition(
        "EZ-Bar Drag Curl",
        "curl",
        "Pull the elbows back as the EZ-bar travels close to the torso.",
    ),
    _SeedDefinition(
        "EZ-Bar Close-Grip Floor Press",
        "floor_press",
        "Use the close angled grips and press from a soft upper-arm touch on the floor.",
    ),
    _SeedDefinition(
        "EZ-Bar JM Press",
        "triceps",
        "Lower the bar toward the upper chest or chin by letting the elbows bend forward, then extend.",
    ),
    _SeedDefinition(
        "Pull-Up Bar Dead Hang",
        "hang",
        "Use a comfortable overhand grip and hold a quiet straight-arm hang.",
    ),
    _SeedDefinition(
        "Pull-Up Flexed-Arm Hang",
        "hang",
        "Hold the chin above the bar with bent elbows, then step down before losing control.",
    ),
    _SeedDefinition(
        "Band Chest Press",
        "cable_press",
        "Anchor the band behind the body and press both handles forward from chest height.",
    ),
    _SeedDefinition(
        "Band Squat",
        "band_squat",
        "Stand on the band and hold it at the shoulders as you squat against increasing tension.",
    ),
    _SeedDefinition(
        "Band Split Squat",
        "band_cable_lunge",
        "Secure the band under the front foot and move through a fixed split stance.",
    ),
    _SeedDefinition(
        "Band Romanian Deadlift",
        "band_cable_hinge",
        "Stand on the band and hinge while keeping its handles close to the legs.",
    ),
    _SeedDefinition(
        "Band Hamstring Curl",
        "hamstring_curl",
        "Anchor the band low and curl the heel toward the glute without lifting the hip.",
    ),
    _SeedDefinition(
        "Band Dead Bug Pulldown",
        "floor_core",
        "Hold the anchored band over the chest while extending one leg without arching the back.",
    ),
    _SeedDefinition(
        "Band Anti-Rotation Hold",
        "anti_rotation",
        "Hold the band at arm's length for the planned time without turning toward the anchor.",
    ),
    _SeedDefinition(
        "Band Shoulder Dislocate",
        "mobility_shoulder",
        "Use a wide band grip and move it overhead only through a smooth shoulder range.",
    ),
    _SeedDefinition(
        "Cable Chest Press",
        "cable_press",
        "Press both cable handles forward together from a balanced split stance.",
    ),
    _SeedDefinition(
        "Cable Rear Delt Row",
        "cable_row",
        "Row toward the upper chest with elbows wide to emphasize the rear shoulders.",
    ),
    _SeedDefinition(
        "Cable 90/90 External Rotation",
        "shoulder_rotation",
        "Keep the upper arm at shoulder height and rotate the forearm backward against light cable tension.",
    ),
    _SeedDefinition(
        "Cable Lateral Lunge",
        "band_cable_lunge",
        "Stand side-on, hold the cable at the chest, and step away from the stack into the working hip.",
    ),
    _SeedDefinition(
        "Cable Romanian Deadlift",
        "band_cable_hinge",
        "Face the low cable and hinge while the handle stays close between the legs.",
    ),
    _SeedDefinition(
        "Cable Kickback",
        "cable_kickback",
        "Brace against the frame and extend one leg behind without arching the lower back.",
    ),
    _SeedDefinition(
        "Cable Anti-Rotation Hold",
        "anti_rotation",
        "Hold the cable handle away from the chest while resisting any turn toward the stack.",
    ),
    _SeedDefinition(
        "Rope Cable Curl",
        "curl",
        "Curl the rope toward the shoulders and keep the palms facing each other.",
    ),
    _SeedDefinition(
        "Treadmill Recovery Walk",
        "treadmill",
        "Choose an easy pace and low incline that keep breathing relaxed throughout.",
    ),
    _SeedDefinition(
        "Treadmill Easy Intervals",
        "treadmill",
        "Alternate gentle brisk segments with comfortable walking recoveries.",
    ),
    _SeedDefinition(
        "Bike Easy Spin",
        "bike",
        "Pedal with light resistance and an easy cadence that stays smooth.",
    ),
    _SeedDefinition(
        "Bike Cadence Drill",
        "bike",
        "Practice the planned cadence changes while keeping resistance light enough to avoid bouncing.",
    ),
)


def _exact(
    overview: str,
    setup_one: str,
    setup_two: str,
    execution_one: str,
    execution_two: str,
    cue_one: str,
    cue_two: str,
    mistake_one: str,
    mistake_two: str,
    safety: str,
) -> ExerciseInstructionSeed:
    return _template(
        overview,
        (setup_one, setup_two),
        (execution_one, execution_two),
        (cue_one, cue_two),
        (mistake_one, mistake_two),
        (safety,),
    )


_EXACT_SEED_OVERRIDES = {
    "Push-Up": _exact(
        "builds chest, shoulder, triceps, and trunk strength in a moving plank.",
        "Place both hands on the floor slightly wider than the shoulders.",
        "Extend both legs and brace a straight line from head through heels.",
        "Bend both elbows diagonally back and lower the chest toward the floor.",
        "Press the floor away until the elbows are straight and the full plank is restored.",
        "Move the ribs and hips as one unit.",
        "Keep the neck long and the hands rooted through the whole palm.",
        "Letting the hips sag before the chest reaches the floor.",
        "Flaring the elbows straight out from the shoulders.",
        "Elevate the hands if a floor push-up cannot be controlled without shoulder pain.",
    ),
    "Barbell Squat": _exact(
        "builds leg and trunk strength with the bar supported across the upper back.",
        "Set the rack hooks just below shoulder height and place the safeties above the lowest squat depth.",
        "Center the bar across the upper back, stand it out of the rack, and settle a balanced stance.",
        "Brace, then bend the hips and knees together while the bar stays over the middle of the feet.",
        "Drive through both feet and stand with the chest and hips rising together.",
        "Keep each knee tracking in the direction of its toes.",
        "Maintain even pressure through the heel and forefoot of both feet.",
        "Letting the chest collapse so the bar moves ahead of the feet.",
        "Allowing the knees to cave inward during the ascent.",
        "Use rack safeties and a load that remains controlled at the lowest depth.",
    ),
    "Dumbbell Bench Press": _exact(
        "trains the chest, shoulders, and triceps with one dumbbell in each hand on a flat bench.",
        "Set the bench flat, plant both feet, and lie with the head and upper back supported.",
        "Hold one dumbbell over each side of the chest with wrists stacked over elbows.",
        "Lower both dumbbells beside the chest until the upper arms reach a comfortable depth.",
        "Press both dumbbells vertically until the elbows are straight without lifting the shoulders from the bench.",
        "Keep both forearms nearly vertical throughout the press.",
        "Maintain gentle upper-back pressure against the bench.",
        "Letting one dumbbell descend faster than the other.",
        "Drifting the dumbbells toward the face during the press.",
        "Use a load that can be brought into position and set down without losing wrist control.",
    ),
    "Chest-Supported Dumbbell Row": _exact(
        "trains the upper back with both dumbbells while the incline bench supports the torso.",
        "Set the bench to a stable incline and lie chest-down with both feet firmly on the floor.",
        "Hold one dumbbell in each hand and let both arms hang straight below the shoulders.",
        "Pull both elbows back beside the ribs while the chest remains in contact with the bench.",
        "Lower both dumbbells until the arms are straight and the shoulder blades can reach forward.",
        "Keep the neck long and both shoulders away from the ears.",
        "Finish each pull with the elbows rather than lifting the chest.",
        "Peeling the chest away from the bench to finish the row.",
        "Shrugging the shoulders instead of drawing the elbows back.",
        "Confirm the bench is stable before loading both arms.",
    ),
    "Dumbbell Skater Squat": _exact(
        "builds single-leg strength and balance while a dumbbell adds load to the working leg.",
        "Hold one dumbbell at the chest and stand on one foot in front of a low target.",
        "Lift the free foot and reach that leg diagonally behind the standing leg.",
        "Bend the working hip and knee as the free knee travels toward the low target behind you.",
        "Press through the whole working foot to stand without placing the free foot down.",
        "Keep the working knee aligned with its toes.",
        "Keep the pelvis level as the free leg reaches behind.",
        "Turning the repetition into a two-leg lunge.",
        "Pushing off the free foot instead of balancing on the working leg.",
        "Use a higher target or no added load until every repetition is balanced.",
    ),
    "EZ-Bar JM Press": _exact(
        "targets the triceps with a hybrid press and elbow bend performed from a flat bench.",
        "Lie on a flat bench with both feet planted and hold the EZ-bar over the shoulders.",
        "Use a close angled grip with straight wrists and begin with both elbows extended.",
        "Let the elbows travel slightly forward as they bend and lower the bar toward the upper chest.",
        "Extend the elbows to return the bar over the shoulders without turning the motion into a chest press.",
        "Keep both sides of the bar level.",
        "Use a short, controlled path that keeps tension on the triceps.",
        "Flaring the elbows wide like a bench press.",
        "Lowering the bar toward the forehead like a skull crusher.",
        "Start light and stop if the elbow path causes joint pain.",
    ),
    "Pull-Up Bar Dead Hang": _exact(
        "develops grip endurance and tolerance in a quiet straight-arm hang.",
        "Place a step beneath a secure pull-up bar and take a comfortable overhand grip.",
        "Step off gradually until both arms are straight and the body hangs without swinging.",
        "Maintain the straight-arm hang while breathing steadily and keeping the body quiet.",
        "Place both feet back on the step before the grip begins to open.",
        "Keep the head between the arms instead of reaching the chin forward.",
        "Use only the shoulder position that remains comfortable under body weight.",
        "Swinging the legs to extend the hold.",
        "Dropping from the bar after the grip is exhausted.",
        "End the hold immediately if the shoulder feels unstable, pinched, or painful.",
    ),
    "Band Anti-Rotation Hold": _exact(
        "trains the trunk to remain square while a resistance band pulls from the side.",
        "Anchor the band securely at chest height and stand side-on with feet about shoulder width.",
        "Hold the band at the chest with both hands, then step away until light side tension is present.",
        "Extend both arms in front of the chest without letting the torso turn toward the anchor.",
        "Hold that arm's-length position for the interval, then return both hands to the chest under control.",
        "Keep the hips and shoulders facing straight ahead.",
        "Breathe behind the brace without leaning away from the band.",
        "Rotating toward the anchor as the arms extend.",
        "Using a band tension that pulls the feet out of position.",
        "Inspect the band and anchor before placing the torso beside the line of pull.",
    ),
    "Cable 90/90 External Rotation": _exact(
        "trains controlled external shoulder rotation with the upper arm held at shoulder height.",
        "Set the cable pulley at elbow height and stand facing the stack with light resistance.",
        "Raise the working upper arm sideways to shoulder height and bend that elbow to 90 degrees.",
        "Rotate the forearm backward until it approaches vertical while the upper arm stays level.",
        "Return the forearm forward slowly without letting the elbow drop or the torso turn.",
        "Keep the shoulder down and centered as the forearm rotates.",
        "Use a small range that the upper arm can hold without compensation.",
        "Arching the lower back to create more rotation.",
        "Letting the elbow drift below shoulder height.",
        "Use very light resistance and stop if the shoulder feels pinched or painful.",
    ),
    "Barbell Hip Hinge Drill": _exact(
        "uses a light barbell to teach a hip hinge while the spine and knee angle stay controlled.",
        "Stand tall with the feet about hip width and hold a light bar against the thighs.",
        "Soften the knees, brace the trunk, and pull the bar gently toward the body.",
        "Push the hips backward while sliding the bar down the thighs without adding a squat.",
        "Stop when the hamstrings tighten, then press the feet down and bring the hips forward to stand.",
        "Keep the bar in contact with the legs.",
        "Maintain the same slight knee bend through the practice-range hinge.",
        "Bending the knees deeply and turning the drill into a squat.",
        "Reaching the bar lower by rounding the back.",
        "Keep the bar light enough that position, not load, remains the focus.",
    ),
    "Treadmill Easy Intervals": _exact(
        "alternates brisk walking with easy walking recovery to build low-intensity conditioning.",
        "Attach the safety clip, step onto the stopped belt, and begin at a comfortable walking speed.",
        "Keep the incline low and identify separate brisk and recovery speeds before the first interval.",
        "Increase to the brisk walking speed for the work interval while keeping breathing controlled.",
        "Reduce to the easy walking speed for recovery and repeat only after balance and breathing settle.",
        "Walk near the center of the belt with a natural arm swing.",
        "Keep both speeds low enough that the rails are not needed for balance.",
        "Turning the brisk segment into a run.",
        "Changing speed while holding body weight on the rails.",
        "Slow the belt to an easy walk before ending the session or stepping off.",
    ),
    "Bike Cadence Drill": _exact(
        "practices smooth changes in pedaling speed while resistance remains light and controlled.",
        "Adjust the seat so the knee remains slightly bent at the bottom of each pedal stroke.",
        "Secure both feet, select light resistance, and begin at an easy cadence.",
        "Increase cadence gradually for the drill interval while keeping the hips quiet on the seat.",
        "Return to the easy cadence for recovery before beginning the next increase.",
        "Relax the hands and shoulders while the legs turn smoothly.",
        "Keep both knees tracking forward without bouncing the hips.",
        "Using so little resistance that the pedals feel uncontrolled.",
        "Chasing cadence after the hips begin to bounce on the seat.",
        "Slow the pedals before adjusting the bike or dismounting.",
    ),
    "Scapular Push-Up": _exact(
        "trains shoulder-blade control while both elbows remain straight in a high plank.",
        "Place both hands under the shoulders and extend the legs into a high plank.",
        "Lock the elbows softly and brace the ribs and hips in one line.",
        "Let the chest sink a few centimeters as the shoulder blades move toward each other.",
        "Press the floor away to spread the shoulder blades without bending the elbows.",
        "Keep the head and hips still as the shoulder blades move.",
        "Use a small range driven only by the upper back.",
        "Turning the repetition into a push-up by bending the elbows.",
        "Dropping the hips as the chest moves toward the floor.",
        "Elevate the hands if the wrists or shoulders cannot tolerate the high-plank position.",
    ),
    "One-Arm Dumbbell Row": _exact(
        "trains one side of the back while the opposite hand and knee support the torso on a bench.",
        "Place the nonworking hand and knee on the bench and keep the working foot on the floor.",
        "Hold one dumbbell below the working shoulder with the spine long and hips square.",
        "Pull the working elbow toward the hip without rotating the torso.",
        "Lower the dumbbell until the arm is straight and the shoulder blade can reach forward.",
        "Keep the working shoulder away from the ear.",
        "Maintain three firm support points throughout the set.",
        "Twisting the torso to lift the dumbbell higher.",
        "Pushing off the bench with the supporting arm.",
        "Confirm the bench is stable before placing body weight on it.",
    ),
    "Dumbbell Renegade Row": _exact(
        "combines a high plank with a one-arm dumbbell row while the trunk resists rotation.",
        "Place two stable dumbbells under the shoulders and take a wide-foot high-plank stance.",
        "Grip both handles with straight wrists and brace the ribs and hips before lifting either weight.",
        "Press one dumbbell into the floor while rowing the other beside the ribs.",
        "Return the lifted dumbbell softly, rebrace, and repeat with the other arm.",
        "Keep the hips facing the floor throughout each row.",
        "Shift as little weight as possible between the feet and supporting hand.",
        "Rolling the torso open to create room for the dumbbell.",
        "Using round dumbbells that can roll under the supporting hand.",
        "Use stable flat-sided dumbbells and stop if the supporting wrist loses control.",
    ),
    "Barbell Good Morning": _exact(
        "trains the posterior chain with the bar fixed across the upper back during a standing hinge.",
        "Set the rack near shoulder height and position the bar securely across the upper back.",
        "Unrack the bar, settle a hip-width stance, soften the knees, and brace the trunk.",
        "Push the hips backward while the torso inclines and the bar remains fixed on the upper back.",
        "Stop when the hamstrings tighten, then drive the hips forward to stand tall.",
        "Maintain the same slight knee bend through the hinge.",
        "Keep pressure balanced over the middle of both feet.",
        "Squatting downward instead of sending the hips back.",
        "Rounding the spine to chase a lower torso position.",
        "Use rack safeties and begin with a light bar until the hinge is consistent.",
    ),
    "Cable Woodchop": _exact(
        "trains coordinated trunk and hip rotation against a cable moving diagonally across the body.",
        "Set the cable above shoulder height and stand side-on with both hands on the handle.",
        "Step away until the cable is taut and brace with the feet wider than hip width.",
        "Pull the handle diagonally down and across while the hips and torso rotate together.",
        "Return along the same diagonal under control before beginning the next repetition.",
        "Pivot the rear foot so the knee follows the turning hip.",
        "Keep both arms long without letting them pull independently of the torso.",
        "Moving only the arms while the hips remain locked.",
        "Letting the cable snap the torso back toward the stack.",
        "Confirm the cable attachment is secure and use a load that permits a controlled return.",
    ),
    "Band Woodchop": _exact(
        "trains coordinated trunk and hip rotation against a band moving diagonally across the body.",
        "Anchor the band above shoulder height and stand side-on with both hands around it.",
        "Step away until the band is taut and brace with the feet wider than hip width.",
        "Pull the band diagonally down and across while the hips and torso rotate together.",
        "Return along the same diagonal without letting the band pull the body off balance.",
        "Pivot the rear foot so the knee follows the turning hip.",
        "Keep both arms long and connected to the torso turn.",
        "Moving only the arms while the hips remain locked.",
        "Standing too close to the anchor to maintain tension.",
        "Inspect the band and anchor before placing the body beside the line of pull.",
    ),
    "Stability Ball Hamstring Curl": _exact(
        "trains both hamstrings by bending the knees while the heels roll a stability ball.",
        "Lie faceup with both heels centered on the ball and both arms resting on the floor.",
        "Lift the hips until the shoulders, hips, and heels form a straight line.",
        "Bend both knees to roll the ball toward the hips without letting the pelvis drop.",
        "Extend both legs to roll the ball away, then lower the hips only after the set.",
        "Keep equal pressure through both heels.",
        "Move the ball slowly enough that it stays centered beneath the legs.",
        "Dropping the hips as the knees bend.",
        "Pulling the ball with one leg faster than the other.",
        "Use a non-slip floor and clear space around the ball before lifting the hips.",
    ),
    "Band Hamstring Curl": _exact(
        "isolates one hamstring by bending the knee against a low anchored resistance band.",
        "Anchor the band near floor level and secure its free end around one ankle.",
        "Lie face down with both hips level and enough distance to create light band tension.",
        "Bend the working knee and bring the heel toward the glute without lifting the thigh.",
        "Straighten the knee slowly until the leg returns to the floor under band tension.",
        "Keep the pelvis pressed evenly into the floor.",
        "Move only the lower leg while the working thigh stays quiet.",
        "Arching the lower back to pull the heel farther.",
        "Letting the band snap the leg straight on the return.",
        "Inspect the band and low anchor before attaching it to the ankle.",
    ),
}


_BLOCKED_MARKERS = (
    "TODO",
    "PLACEHOLDER",
    "SAME AS",
    "SPECIFIED",
    "REQUIRED",
    "CHOSEN",
    "SPECIFIED POSITION",
    "REQUIRED POSITION",
    "REQUIRED PATH",
    "SPECIFIED GRIP",
    "SPECIFIED SQUAT STYLE",
    "CHOSEN SHOULDER POSITION",
    "PRESS, HOLD, OR GUIDE",
    "EASY, STEADY, TEMPO, OR INTERVAL",
)


def _build_seed_data() -> dict[str, ExerciseInstructionSeed]:
    seeds: dict[str, ExerciseInstructionSeed] = {}
    for definition in _SEED_DEFINITIONS:
        if definition.name in seeds:
            raise ValueError(f"Duplicate exercise instruction seed: {definition.name}")
        exact_override = _EXACT_SEED_OVERRIDES.get(definition.name)
        if exact_override is None:
            template = _TEMPLATES[definition.template_key]
            seed = ExerciseInstructionSeed(
                overview=f"{definition.name} {template.overview}",
                setup_steps=template.setup_steps,
                execution_steps=(definition.distinctive_step,),
                form_cues=template.form_cues,
                common_mistakes=template.common_mistakes,
                safety_notes=template.safety_notes,
            )
        else:
            seed = ExerciseInstructionSeed(
                overview=f"{definition.name} {exact_override.overview}",
                setup_steps=exact_override.setup_steps,
                execution_steps=exact_override.execution_steps,
                form_cues=exact_override.form_cues,
                common_mistakes=exact_override.common_mistakes,
                safety_notes=exact_override.safety_notes,
            )
        fields = (
            seed.overview,
            *seed.setup_steps,
            *seed.execution_steps,
            *seed.form_cues,
            *seed.common_mistakes,
            *seed.safety_notes,
        )
        if any(not value.strip() for value in fields):
            raise ValueError(
                f"Blank exercise instruction seed content: {definition.name}"
            )
        upper_fields = tuple(value.upper() for value in fields)
        if any(
            marker in value for marker in _BLOCKED_MARKERS for value in upper_fields
        ):
            raise ValueError(
                f"Placeholder exercise instruction seed: {definition.name}"
            )
        seeds[definition.name] = seed
    return seeds


EXERCISE_INSTRUCTION_SEEDS = _build_seed_data()
