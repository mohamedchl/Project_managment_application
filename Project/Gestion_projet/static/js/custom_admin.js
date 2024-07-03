document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        form.addEventListener('submit', async function(event) {
            event.preventDefault();

            const ressourceIdInput = form.querySelector('#id_ressource');
            const dateDebutInput = form.querySelector('#id_date_debut'); // Assuming the date_debut input has this ID
            const dateFinInput = form.querySelector('#id_date_fin');     // Assuming the date_fin input has this ID
            const IdInput = form.querySelector('#id_id_TR');     // Assuming the date_fin input has this ID
            const ressourceId = ressourceIdInput ? ressourceIdInput.value : null;
            const dateDebut = dateDebutInput ? dateDebutInput.value : null;
            const dateFin = dateFinInput ? dateFinInput.value : null;
            const IDTR = IdInput ? IdInput.value : null;
            console.log("id="+IDTR)
            if (!ressourceId || !dateDebut || !dateFin) {
                console.error('Resource ID or dates are not defined');
                return;
            }
           

            try {
                const response = await fetch(`/api/utilisation-ressource/${ressourceId}/?date_debut=${dateDebut}&date_fin=${dateFin}&id_TR=${IDTR}`);
                if (!response.ok) {
                    console.error('Error fetching ressource details');
                    return;
                }
                const data = await response.json();
                console.log("Received data:", data);

                if (data.overlap) {
                    const modalContent = data.message;
                    showModal(modalContent, data.overlap_dates);
                } else {
                    form.submit(); // Allow form submission if no overlap
                }
            } catch (error) {
                console.error('There was a problem with the fetch operation:', error);
            }
        });
    });

    function showModal(content, overlapDates) {
        let modal = document.getElementById('modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'modal';
            modal.style.display = 'none'; // Start hidden for proper show/hide control
            modal.style.position = 'fixed';
            modal.style.zIndex = '1000';
            modal.style.left = '0';
            modal.style.top = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.overflow = 'auto';
            modal.style.backgroundColor = 'rgba(0,0,0,0.4)';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';
            modal.style.opacity = '0';  // Start hidden for animation
            modal.style.transition = 'opacity 0.5s'; // Transition for fade-in effect

            modal.innerHTML = `
                <div class="modal-content" style="padding: 20px; width: 40%; background-color: #fff; border: 1px solid #888; box-shadow: 0 5px 15px rgba(0,0,0,0.3); position: relative; transform: translateX(0);">
                    <h2 class="modal-title" style="color: orange; text-align: center;">Warning</h2>
                    <p class="modal-message" style="color:black;">${content}</p>
                    <p class="modal-message" style="color:black;">Les dates ou ce ressource est Louer sont :</p>
                    <ul class="utilisation-dates" style="list-style-type: none; padding: 0;"></ul>
                    <p class="modal-message" style="color:black;">Vous devez choisir des nouvelles dates pour l'utilisation</p>
                    <div class="modal-footer" style="text-align: center; margin-top: 20px;">
                        <button class="modal-close btn" style="background-color: #f44336; color: white; padding: 10px 20px; border: none; cursor: pointer;">Close</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        }

        const modalContent = modal.querySelector('.modal-content');
        modal.querySelector('.modal-message').textContent = content;
        if (overlapDates && overlapDates.length > 0) {
            const utilisationDates = modalContent.querySelector('.utilisation-dates');
            const datesList = overlapDates.map(date => `<li class="date" style="color:black;">De <span style="font-weight: 800; color: orange;">${date.date_debut}</span> à <span style="font-weight: 800; color: orange;">${date.date_fin}</span></li>`).join('');
            utilisationDates.innerHTML = datesList;
        }

        // Display the modal
        modal.style.display = 'flex';
        // Trigger the fade-in effect
        setTimeout(() => { modal.style.opacity = '1'; }, 10);

        const closeButton = modal.querySelector('.modal-close');
        closeButton.addEventListener('click', function() {
            // Add fade-out effect
            modal.style.opacity = '0';
            setTimeout(() => {
                modal.style.display = 'none';
            }, 500); // Match this timeout with the transition duration
        }, { once: true });
    }
});
