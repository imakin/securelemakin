describe('Securelemakin service test', () => {
    it('test POST', () => {
      cy.visit('http://192.168.0.12/');
      cy.fingerprint();
      
      cy.get('#new_name').type('test_post_2');
      cy.get('#new_message').type('test message from cypress');
      cy.fixture('secret_makin.json').then((secret_makin)=>{
        console.log(secret_makin['vulcrypted_new_key']);
        cy.vulnerable_decrypt_type(secret_makin['vulcrypted_new_key'],'#new_key')
      });
      cy.get('form#new-data button').click();

      cy.wait(5000)
      cy.visit('http://192.168.0.12/');
    })
  })
  